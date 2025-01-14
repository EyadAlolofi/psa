import frappe, json
import datetime as dt
from datetime import datetime as DateTime
from frappe import _


@frappe.whitelist()
def get_student_for_current_user():
    user = frappe.session.user
    student = frappe.get_value("Student", {"user_id": user}, "name")
    return student


@frappe.whitelist()
def get_program_enrollment_for_current_user():
    student = get_student_for_current_user()
    program_enrollment = frappe.get_value("Program Enrollment", {"student": student, "enabled": 1}, "name")
    return program_enrollment


@frappe.whitelist()
def get_program_enrollment_for_student(student):
    program_enrollment = frappe.get_value("Program Enrollment", {"student": student, "enabled": 1}, "name")
    return program_enrollment


@frappe.whitelist()
def get_student_supervisor_for_student_and_program_enrollment(student, program_enrollment):
    student_supervisor = frappe.get_value("Student Supervisor", {"student": student, "program_enrollment": program_enrollment, "enabled": 1, "status": "Active", "type": "Main Supervisor"}, "name")
    return student_supervisor


@frappe.whitelist()
def get_student_research_for_student_and_program_enrollment(student, program_enrollment):
    student_research = frappe.get_value("Student Research", {"student": student, "program_enrollment": program_enrollment, "enabled": 1, "status": "Active"}, "name")
    return student_research


@frappe.whitelist()
def get_url_to_new_form(doctype_name):
    return frappe.utils.get_url_to_form(doctype_name, "new")


@frappe.whitelist()
def get_current_workflow_role(doctype_workflow_name, current_status):
	doc = frappe.get_doc('Workflow', doctype_workflow_name)
	states = doc.states
	for state in states:
		if state.state == current_status:
			return state.allow_edit


@frappe.whitelist()
def insert_new_timeline_child_table(doctype_name, doc_name, timeline_child_table_name, dictionary_of_values):
	try:
		if dictionary_of_values:
			dictionary = json.loads(dictionary_of_values)
			
			doc = frappe.get_doc(doctype_name, doc_name)
			new_row = doc.append(timeline_child_table_name, {})

			new_row.position = dictionary['position']
			new_row.full_name = dictionary['full_name']
			new_row.previous_status = dictionary['previous_status']
			new_row.received_date = dictionary['received_date']
			new_row.action = dictionary['action']
			new_row.next_status = dictionary['next_status']
			new_row.action_date = dictionary['action_date']

			doc.save()
			return True
		else:
			frappe.throw("Error: dictionary_of_values is empty!")
	except Exception as e:
		frappe.throw(f"An error occurred: {str(e)}")


@frappe.whitelist()
def get_program_enrollment_status(program_enrollment):
    program_enrollment_status = frappe.get_value("Program Enrollment", {"name": program_enrollment}, "status")
    return program_enrollment_status


@frappe.whitelist()
def check_program_enrollment_status(program_enrollment, accepted_status_list, rejected_status_list):
	status = get_program_enrollment_status(program_enrollment)
	if status in accepted_status_list:
		return [True, status]
	elif status in rejected_status_list:
		return [False, status]
	else:
		return [False, status]


@frappe.whitelist()
def active_request(doctype_name, student, program_enrollment, docstatus_list, status_list):
	try:
		fields = "SELECT {0} ".format("*")
		doctype = "FROM `tab{0}` ".format(doctype_name)
		where = "WHERE `student` = '{0}' AND `program_enrollment` = '{1}' ".format(student, program_enrollment)
		if docstatus_list:
			where_docstatus = ""
			for docstatus in docstatus_list:
				if where_docstatus != "":
					where_docstatus = where_docstatus + " OR `docstatus` = " + str(docstatus)
				else:
					where_docstatus = "`docstatus` = " + str(docstatus)
			where = where + "AND ({0}) ".format(where_docstatus)
		if status_list:
			where_status = ""
			for status in status_list:
				if where_status:
					where_status += " OR `status` LIKE '%{0}%'".format(status)
				else:
					where_status += "`status` LIKE '%{0}%'".format(status)
			where += "AND ({0}) ".format(where_status)
		query = fields + doctype + where + "ORDER BY modified DESC LIMIT 1"
		docs = frappe.db.sql(query, as_dict=True)
		return docs[0] if docs else None
	except Exception as e:
		frappe.throw(f"An error occurred: {str(e)}")


@frappe.whitelist()
def check_active_request(student, program_enrollment, doctype_list):
	try:
		doctype_names = [
			"Suspend Enrollment Request",
			"Continue Enrollment Request",
			"Withdrawal Request",
			"Change Research Title Request",
			"Change Research Main Supervisor Request",
			"Change Research Co Supervisor Request",
			"Initial Discussion Request",
			"Extension Request"
		]

		doctype_docstatuses = {
			"Suspend Enrollment Request": [0],
			"Continue Enrollment Request": [0],
			"Withdrawal Request": [0],
			"Change Research Title Request": [0],
			"Change Research Main Supervisor Request": [0],
			"Change Research Co Supervisor Request": [0],
			"Initial Discussion Request": [0],
			"Extension Request": [0]
		}

		doctype_statuses = {
			"Suspend Enrollment Request": ["Draft", "Pending"],
			"Continue Enrollment Request": ["Draft", "Pending"],
			"Withdrawal Request": ["Draft", "Pending"],
			"Change Research Title Request": ["Draft", "Pending"],
			"Change Research Main Supervisor Request": ["Draft", "Pending"],
			"Change Research Co Supervisor Request": ["Draft", "Pending"],
			"Initial Discussion Request": ["Draft", "Pending"],
			"Extension Request": ["Draft", "Pending"]
		}

		if isinstance(doctype_list, str):
			for doctype in json.loads(doctype_list):
				if doctype in doctype_names:
					active_request_doc = active_request(doctype_name=doctype, student=student, program_enrollment=program_enrollment, docstatus_list=doctype_docstatuses[doctype], status_list=doctype_statuses[doctype])
					if active_request_doc:
						return [doctype, active_request_doc]
					else:
						continue
				else:
					continue

		elif isinstance(doctype_list, list):
			for doctype in json.loads(json.dumps(doctype_list)):
				if doctype in doctype_names:
					active_request_doc = active_request(doctype_name=doctype, student=student, program_enrollment=program_enrollment, docstatus_list=doctype_docstatuses[doctype], status_list=doctype_statuses[doctype])
					if active_request_doc:
						return [doctype, active_request_doc]
					else:
						continue
				else:
					continue

	except Exception as e:
		frappe.throw(f"An error occurred: {str(e)}")


@frappe.whitelist()
def get_scientific_degree(scientific_degree):
	query = """
	select fm.name from
		`tabFaculty Member Scientific Qualification` as fmsq
		join `tabFaculty Member` as fm
		on fmsq.parent = fm.name
		where fmsq.scientific_degree = %s;
	"""
	docs = frappe.db.sql(query, (scientific_degree), as_dict=True)
	return docs if docs else None


@frappe.whitelist()
def get_researcher_meetings(student, program_enrollment, from_date, to_date):
	researcher_meetings = frappe.db.get_all("Researcher Meeting", filters={"student": student, "program_enrollment": program_enrollment, "meeting_date": ["between", [from_date, to_date]]}, fields=["name", "meeting_date"], order_by="meeting_date asc")
	return researcher_meetings


@frappe.whitelist(allow_guest=True)
def format_date(date_value):
    """Format date as string or return '--' if None."""
    if isinstance(date_value, dt.date):
        return date_value.strftime('%Y-%m-%d')
    return "--"


@frappe.whitelist(allow_guest=True)
def get_program_enrollment_information(student, program_enrollment):
    try:
        # Get student information
        student_information = frappe.db.get_all(
            "Student",
            filters={"name": student},
            fields=['first_name', 'middle_name', 'last_name', 'first_name_en', 'middle_name_en', 'last_name_en'],
            ignore_permissions=True
        )

        if student_information:
            student_info = student_information[0]
            full_name_arabic = ' '.join(filter(None, [student_info.get('first_name'), student_info.get('middle_name'), student_info.get('last_name')]))
            full_name_english = ' '.join(filter(None, [student_info.get('first_name_en'), student_info.get('middle_name_en'), student_info.get('last_name_en')]))
        else:
            full_name_arabic = "--"
            full_name_english = "--"

        # Get program enrollment information
        program_enrollment_information = frappe.db.get_all(
            "Program Enrollment",
            filters={"name": program_enrollment},
            fields=['enrollment_date', 'faculty', 'program', 'status'],
            ignore_permissions=True
        )

        if program_enrollment_information:
            program_enrollment_info = program_enrollment_information[0]
            enrollment_date = format_date(program_enrollment_info.get('enrollment_date')) or "--"
            program_enrollment_faculty = program_enrollment_info.get('faculty') or "--"
            program = program_enrollment_info.get('program') or "--"
            status = program_enrollment_info.get('status') or "--"
        else:
            enrollment_date = "--"
            program_enrollment_faculty = "--"
            program = "--"
            status = "--"

        # Get program specification information
        program_specification_information = frappe.db.get_all(
            "Program Specification",
            filters={"name": program},
            fields=['program_name', 'faculty', 'faculty_department', 'program_degree'],
            ignore_permissions=True
        )

        if program_specification_information:
            program_specification_info = program_specification_information[0]
            program_name = program_specification_info.get('program_name') or "--"
            program_faculty = program_specification_info.get('faculty') or "--"
            program_faculty_department = program_specification_info.get('faculty_department') or "--"
            program_degree = program_specification_info.get('program_degree') or "--"
        else:
            program_name = "--"
            program_faculty = "--"
            program_faculty_department = "--"
            program_degree = "--"

        # Get student research information
        student_research_information = frappe.db.get_all(
            "Student Research",
            filters={
                "enabled": 1,
                "status": "Active",
                "student": student,
                "program_enrollment": program_enrollment
            },
            fields=['research_title_arabic', 'research_title_english', 'date_of_approval_of_the_research_title'],
            ignore_permissions=True
        )

        if student_research_information:
            student_research_info = student_research_information[0]
            research_title_arabic = student_research_info.get('research_title_arabic') or "--"
            research_title_english = student_research_info.get('research_title_english') or "--"
            date_of_approval_of_the_research_title = format_date(student_research_info.get('date_of_approval_of_the_research_title')) or "--"
        else:
            research_title_arabic = "--"
            research_title_english = "--"
            date_of_approval_of_the_research_title = "--"

        # Get main supervisor information
        main_supervisor_information = frappe.db.get_all(
            "Student Supervisor",
            filters={
                "enabled": 1,
                "status": "Active",
                "student": student,
                "program_enrollment": program_enrollment,
                "type": "Main Supervisor"
            },
            fields=['name', 'supervisor', 'supervisor_name', 'supervisor_appointment_date'],
            ignore_permissions=True
        )

        if main_supervisor_information:
            main_supervisor_info = main_supervisor_information[0]
            main_student_supervisor_id = main_supervisor_info.get('name') or "--"
            main_supervisor_faculty_member = main_supervisor_info.get('supervisor') or "--"
            main_supervisor_name_arabic = main_supervisor_info.get('supervisor_name') or "--"
            main_supervisor_appointment_date = format_date(main_supervisor_info.get('supervisor_appointment_date')) or "--"
        else:
            main_student_supervisor_id = "--"
            main_supervisor_faculty_member = "--"
            main_supervisor_name_arabic = "--"
            main_supervisor_appointment_date = "--"

        # Get faculty member information for main supervisor
        faculty_member_information = frappe.db.get_all(
            "Faculty Member",
            filters={"name": main_supervisor_faculty_member},
            fields=['faculty', 'faculty_member_name_english', 'academic_rank'],
            ignore_permissions=True
        )

        if faculty_member_information:
            faculty_member_info = faculty_member_information[0]
            main_supervisor_faculty_member_faculty = faculty_member_info.get('faculty') or "--"
            main_supervisor_name_english = faculty_member_info.get('faculty_member_name_english') or "--"
            main_supervisor_academic_rank = faculty_member_info.get('academic_rank') or "--"
        else:
            main_supervisor_faculty_member_faculty = "--"
            main_supervisor_name_english = "--"
            main_supervisor_academic_rank = "--"

        # Get co-supervisor information
        co_supervisor_information = frappe.db.get_all(
            "Student Supervisor",
            filters={
                "enabled": 1,
                "status": "Active",
                "student": student,
                "program_enrollment": program_enrollment,
                "type": "Co-Supervisor"
            },
            fields=['name', 'supervisor', 'supervisor_name', 'supervisor_appointment_date'],
            ignore_permissions=True
        )

        co_supervisors = []
        for co_supervisor in co_supervisor_information:
            co_supervisors.append({
                'name': co_supervisor.get('supervisor_name') or "--",
                'appointment_date': format_date(co_supervisor.get('supervisor_appointment_date')) or "--"
            })

        return {
            "full_name_arabic": full_name_arabic,
            "full_name_english": full_name_english,
            "enrollment_date": enrollment_date,
            "program_enrollment_faculty": program_enrollment_faculty,
            "program": program,
            "status": status,
            "program_name": program_name,
            "program_faculty": program_faculty,
            "program_faculty_department": program_faculty_department,
            "program_degree": program_degree,
            "research_title_arabic": research_title_arabic,
            "research_title_english": research_title_english,
            "date_of_approval_of_the_research_title": date_of_approval_of_the_research_title,
            "main_student_supervisor_id": main_student_supervisor_id,
            "main_supervisor_faculty_member": main_supervisor_faculty_member,
            "main_supervisor_name_arabic": main_supervisor_name_arabic,
            "main_supervisor_appointment_date": main_supervisor_appointment_date,
            "main_supervisor_faculty_member_faculty": main_supervisor_faculty_member_faculty,
            "main_supervisor_name_english": main_supervisor_name_english,
            "main_supervisor_academic_rank": main_supervisor_academic_rank,
            "co_supervisors": co_supervisors
        }

    except Exception as e:
        return {"error": f"An error occurred in fetching information: {str(e)}"}


@frappe.whitelist()
def get_students_by_supervisor():
    user_id = frappe.session.user

    employee = frappe.db.get_value('Employee', {'user_id': user_id}, 'name')
    if not employee:
        frappe.throw(_("No Employee found for the current user."))

    supervisor = frappe.db.get_value('Faculty Member', {'employee': employee}, 'name')
    if not supervisor:
        frappe.throw(_("No Supervisor found for the employee."))

    students = frappe.db.sql("""
        SELECT DISTINCT student.name
        FROM `tabStudent` AS student
        JOIN `tabStudent Supervisor` AS supervisor
        ON student.name = supervisor.student
        WHERE supervisor.supervisor = %s
    """, (supervisor,), as_dict=True)

    return students


@frappe.whitelist()
def get_single_value(doctype_name, field):
    result = frappe.db.get_single_value(doctype_name, str(field))
    return result


@frappe.whitelist()
def is_parent_category(category_name, sub_category_name):
    try:
        parent_category = frappe.get_doc("Transaction Category", {"category_name": category_name})    
        sub_category = frappe.get_doc("Transaction Category", {"category_name": sub_category_name})
        if sub_category.parent_category == parent_category.name:
            return True
        else:
            return False
    except Exception as e:
        return {"error": f"An error occurred in fetching information: {str(e)}"}


@frappe.whitelist()
def get_template_by_category(category_name):
    try:
        category = frappe.get_doc("Transaction Category", category_name)
        template = frappe.get_doc("Transaction Category Template", category.template)
        return template
    except Exception as e:
        return {"error": f"An error occurred in fetching information: {str(e)}"}


@frappe.whitelist()
def create_applicants(transaction, applicants_list):
    try:
        for applicant in applicants_list:
            applicant_entry = transaction.append('applicants_table', {})
            applicant_entry.applicant_type = applicant.get('applicant_type')
            applicant_entry.applicant = applicant.get('applicant')
            applicant_entry.applicant_name = applicant.get('applicant_name')
        
        transaction.save()
    except Exception as e:
        return {"error": f"An error occurred while creating applicants: {str(e)}"}


@frappe.whitelist()
def create_transaction(priority, title, category, sub_category, refrenced_document, applicants_list):
    try:
        if(is_parent_category(category, sub_category)):
            template = get_template_by_category(sub_category)

            new_transaction = frappe.new_doc("Transaction")

            new_transaction.transaction_scope = "In Company"
            new_transaction.start_date =  DateTime.now()
            new_transaction.hijri_date =  ""
            new_transaction.priority = priority
            new_transaction.status = "Pending"
            new_transaction.submit_time = DateTime.now()
            new_transaction.title = title
            new_transaction.transaction_description =template.description
            new_transaction.category = category
            new_transaction.sub_category = sub_category
            new_transaction.referenced_doctype = template.template_doctype
            new_transaction.referenced_document = refrenced_document

            new_transaction.insert(ignore_permissions=True)

            if(applicants_list):
                create_applicants(new_transaction, applicants_list) 

            return new_transaction.name
        else:
            return {"error": "Sub-category is not a child of the category"}
    except Exception as e:
        return {"error": f"An error occurred while creating a transaction: {str(e)}"}


@frappe.whitelist()
def create_psa_transaction(doctype_name, doc_name, applicants):
    try:
        # applicant_type: "Student", "Employee", "User", "Academic"
        # applicants = [
        #     { 'applicant_type': "Student", 'applicant': "EDU-STU-2024-000011", 'applicant_name': "Esmail" },
        #     { 'applicant_type': "Employee", 'applicant': "HR-EMP-00001", 'applicant_name': "Ahmed" }
        # ]

        priority = "Low"
        title = doctype_name
        category = "PSA"
        sub_category = doctype_name
        refrenced_document = doc_name
        applicants_list = applicants

        transaction_id = create_transaction(priority, title, category, sub_category, refrenced_document, applicants_list)

        return {"transaction_id": transaction_id}
    except Exception as e:
        return {"error": f"An error occurred while creating a transaction: {str(e)}"}


@frappe.whitelist()
def get_transaction_status(doctype_name, doc_name):
    try:
        transaction = frappe.get_all(
            "Transaction",
            filters={
                "referenced_doctype": doctype_name,
                "referenced_document": doc_name,
                "sub_category": doctype_name
            },
            fields=["name", "status", "creation"],
            order_by="creation",
            limit=1
        )

        return transaction or None
    except Exception as e:
        frappe.throw(_("An error occurred while getting the transaction information: {0}").format(str(e)))


@frappe.whitelist()
def get_transaction_actions_recursion(actions, recipients=[], processed_recipients=None):
    try:
        if processed_recipients is None:
            processed_recipients = set()

        recipient_actions = []
        recipient = None

        for recipient in recipients:
            if recipient.recipient_email in processed_recipients:
                continue
            processed_recipients.add(recipient.recipient_email)
            recipient_dict = {
                "recipient": recipient.recipient_email,
                "action": None,
                "redirected": [],
                "link": None,
            }
            for action in actions:
                if action.owner == recipient.recipient_email and action.auto_redirect == 0:
                    recipient_dict["action"] = action
                    recipient_dict["link"] = get_document_link(
                        "Transaction Action", action.name
                    )
                    if action.type == "Redirected":
                        redirected_recipients = frappe.get_all(
                            "Transaction Recipients",
                            filters={"parent": action.name},
                            fields=["recipient_email"],
                            order_by="creation",
                        )
                        redirected_recipients = [
                            r
                            for r in redirected_recipients
                            if r.recipient_email not in processed_recipients
                        ]
                        recipient_dict["redirected"] = get_transaction_actions_recursion(
                            actions, redirected_recipients, processed_recipients
                        )
            recipient_actions.append(recipient_dict)
        return recipient_actions
    except Exception as e:
        frappe.throw(_("An error occurred while getting the transaction information: {0}").format(str(e)))


@frappe.whitelist()
def get_transaction_actions(transaction_name):
    try:
        actions = frappe.get_all(
            "Transaction Action",
            filters={
                "transaction": transaction_name,
                "docstatus": 1,
            },
            fields=["name", "type", "owner", "auto_redirect"],
            order_by="creation",
        )

        recipients = []
        i = 0
        while i < len(actions):
            action = actions[i]

            if action.auto_redirect == 1:
                new_recipients = frappe.get_all(
                    "Transaction Recipients",
                    filters={"parent": action.name},
                    fields=["recipient_email"],
                    order_by="creation",
                )
                recipients.extend(new_recipients)
                del actions[i]
            else:
                i += 1
        recipient_actions = get_transaction_actions_recursion(actions, recipients)
        return json.dumps(recipient_actions)

    except Exception as e:
        frappe.throw(_("An error occurred while getting the transaction information: {0}").format(str(e)))


@frappe.whitelist()
def get_transaction_information(doctype_name, doc_name):
    transaction = get_transaction_status(doctype_name, doc_name)
    if transaction:
        transaction_name = transaction[0].name
        transaction_status = transaction[0].status
        transaction_date = transaction[0].creation

        ###################################################################################
        # transaction_actions = get_transaction_actions(transaction_name)
        ###################################################################################
        # From the Transaction Jinja Template #
        ###################################################################################
        # {% macro render_recipient(recipient_dict) %}
        #   <div>
        #     {% if recipient_dict.action %}
        #       <a href="{{ recipient_dict.link }}">
        #         <div class="dot 
        #           {% if recipient_dict.action.type == 'Approved' %}approved
        #           {% elif recipient_dict.action.type == 'Redirected' %}redirect
        #           {% elif recipient_dict.action.type == 'Rejected' %}reject
        #           {% else %}pending
        #           {% endif %}"></div>
        #         <span class="recipient">{{ recipient_dict.recipient }} - {{ recipient_dict.action.type }} </span>
        #       </a>
        #     {% else %}
        #       <div class="dot pending"></div>
        #       <span>{{ recipient_dict.recipient }} - Pending</span>
        #     {% endif %}
        #   </div>
        #     {% for redirected_recipient in recipient_dict.redirected %}
        #       <div class="redirected">
        #         {{ render_recipient(redirected_recipient) }}
        #       </div>
        #     {% endfor %}
        # {% endmacro %}

        # {% for recipient_dict in recipient_actions %}
        #   {{ render_recipient(recipient_dict) }}
        # {% endfor %}
        ###################################################################################
        # return transaction_actions
        ###################################################################################

        return {'name': transaction_name, 'date': transaction_date, 'status': transaction_status}
    else:
        return None


# Function to save timeline child table rows (before fixing it by check "In List View" in Timeline Child Table's fields)
# @frappe.whitelist()
# def save_timeline_child_table(doctype_name, doc_name, timeline_child_table_name, timeline_child_table_list):
# 	try:
# 		if timeline_child_table_list:
# 			doc = frappe.get_doc(doctype_name, doc_name)

# 			formated_timeline_child_table_list = json.loads(timeline_child_table_list)
			
# 			for row in formated_timeline_child_table_list:
# 				new_row = doc.append(timeline_child_table_name, {})
				
# 				new_row.position = row['position']
# 				new_row.full_name = row['full_name']
# 				new_row.previous_status = row['previous_status']
# 				new_row.received_date = row['received_date']
# 				new_row.action = row['action']
# 				new_row.next_status = row['next_status']
# 				new_row.action_date = row['action_date']

# 			doc.save()
# 			return True
# 		else:
# 			frappe.throw("Error: timeline_child_table_list is empty!")
# 	except Exception as e:
# 		frappe.throw(f"An error occurred: {str(e)}")
