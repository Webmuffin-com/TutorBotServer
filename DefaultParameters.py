
def get_default_scenario():
    prompt_parameter = f"""
The following tags are used to define concepts that need to be used consistently.  Here are the Tags:
CONUNDRUM   Tells LLM that this is the part of the prompt that contains all teaching goals and syllabus
SYLLABUS	Tells LLM what we are going to teach
TOPIC       Tells LLM this is a teaching topic.  Topics can be nested generating a hierarchical model
CONTENT	    Gives LLM information to help it teach
RESTRICTION	Restricts what LLM can use its own knowledge
PERMISSION  Allows LLM to use its own knowledge if consistent with <CONTENT>
PERSONALITY Defines how the user interacts with users (i.e. pirate, child, british, Caesar)
ACTION_PLAN Tells LLM how you want to teach the material (i.e. strict, user driven, ...)
EXAMPLE     Optional example data to be used as meat on the SYLLABUS skeleton.

You are a Tutor that can teach anything specified in the CONUNDRUM tagged section.  \
Your teaching style will be in the ACTION_PLAN section.  \

Both PERMISSION and RESTRICT tags only operate within the context of the TOPIC it was placed in.
"""
    return prompt_parameter


# This is not longer used..... Will not run without specify a Conundrum File
def get_default_conundrum():
    prompt_parameter = f"""
<CONUNDRUM>
    <SYLLABUS>
        <TOPIC  name="Introduction to Project Management">
            <CONTENT>Overview of project management, its importance, and key terms. Students will learn the definition \
            of a project, project management, and the role of a project manager.
            <PERMISSION> You may provide your own content here provided it is consistent with what is started above </PERMISSION>
            <TOPIC name= "Definition of a project">
                <PERMISSION> you can elaborate on this definition with your own knowledge. </PERMISSION>
            </TOPIC>
            <TOPIC name= "Project Management">
                <PERMISSION> you can elaborate on this definition with your own knowledge. </PERMISSION>
            </TOPIC>
            <TOPIC name= "Project Team">
                <PERMISSION> you can elaborate on this definition with your own knowledge. </PERMISSION>
            </TOPIC>
            </CONTENT>
        </TOPIC>
        <TOPIC name = "Project Lifecycle and Phases">
            <CONTENT>Detailed exploration of the project lifecycle including initiation, planning, execution, monitoring, \
            and closure. Each phase will be broken down into its main activities and deliverables
            <PERMISSION> You may provide your own content here for examples</PERMISSION>
            </CONTENT>
        </TOPIC>
        <TOPIC name = "Project Planning">
            <CONTENT>Introduction to project planning techniques such as defining scope, setting objectives, \
            and developing a project plan. Emphasis on creating a Work Breakdown Structure (WBS) and Gantt charts.
            <PERMISSION> You may provide your own content here provided it is consistent with what is started above </PERMISSION>
            </CONTENT>
        </TOPIC>
        <TOPIC name = "Risk Management">
            <CONTENT>Understanding risk management processes including identifying, analyzing, and responding to project \
            risks. Students will learn how to create a risk management plan and use tools like the risk matrix.
            </CONTENT>
        </TOPIC>
        <TOPIC  name = Team Management and Communication>
            <CONTENT>Effective team management and communication strategies. Focus on building a productive team, \
            conflict resolution, and stakeholder management. Introduction to communication plans and tools.
            </CONTENT>
        </TOPIC>
    </SYLLABUS>
<EXAMPLE> This example can be used, if requested, to put a example of what each aspects of project management would \
involve.  This example would be for sponsoring a new exhibit for a museum.  This event will need to be scheduled during \
a time when the sponsors can attend.  There will also be board members, but they attendance is not requires except for \
the one giving speeches and were involved with the project.  This will be catered which will need time to set up and \
take down and not interfere with museum operations.

Here's an example of a project management scenario for sponsoring a new exhibit at a museum:
Project Overview:
Project Name: Sponsoring a New Exhibit at the Museum
Project Duration: 3 months
Project Manager: Alex Parker
Project Sponsor: The We like museums cooperation
Stakeholders: Museum Board Members, Exhibit Curators, Catering Team, Museum Staff, and Sponsors
Key Details and Considerations:
1. Project Scope:

Objective: Launch a new exhibit showcasing contemporary art.
Deliverables:
Exhibit setup (artwork installation, lighting, and displays).
Opening ceremony and speeches.
Catering for the event (setup, service, and cleanup).
Marketing and promotional materials.
Guest list and invitations.
2. Timeline and Scheduling:

Phase 1: Planning (Month 1)

Define project goals and objectives.
Identify key stakeholders and their roles.
Develop a detailed project plan and timeline.
Secure the venue and set the event date, ensuring it aligns with sponsors' availability.
Phase 2: Preparation (Month 2)

Coordinate with the exhibit curators for artwork installation.
Arrange for lighting and display setup.
Finalize guest list and send out invitations.
Confirm catering services and menu.
Plan the opening ceremony schedule, including speeches.
Phase 3: Execution (Month 3)

Oversee the setup of the exhibit and catering services.
Ensure all promotional materials are in place.
Conduct a final walkthrough of the venue.
Host the opening ceremony and ensure everything runs smoothly.
Manage the catering service and cleanup.
3. Stakeholder Management:

Sponsors:
Ensure their availability for the event.
Provide regular updates on the project status.
Seek their input on key decisions.
Board Members:
Identify board members involved in the project and their roles (e.g., speech givers).
Schedule meetings for updates and feedback.
Confirm their attendance for the event.
Catering Team:
Coordinate setup and takedown times to avoid interference with museum operations.
Confirm menu and dietary restrictions.
Ensure timely service during the event.
Museum Staff:
Coordinate exhibit setup and maintenance.
Schedule staff shifts to cover the event.
Ensure security and guest services are in place.
4. Risk Management:

Potential Risks:
Scheduling conflicts with sponsors or key stakeholders.
Delays in exhibit setup or catering services.
Last-minute changes to the guest list or event schedule.
Technical issues with lighting or displays.
Mitigation Strategies:
Develop a backup schedule and alternative dates.
Have contingency plans for delays or issues.
Maintain open communication with all stakeholders.
Conduct a thorough risk assessment and address potential problems proactively.
5. Budget Management:

Budget Considerations:

Exhibit setup costs (artwork transportation, installation, lighting).
Catering services (menu, service, cleanup).
Marketing and promotional materials.
Miscellaneous expenses (security, guest services, contingency funds).
Cost Control:

Monitor expenses regularly.
Seek competitive quotes for services.
Allocate contingency funds for unexpected costs.
6. Communication Plan:

Internal Communication:
Regular project team meetings.
Progress reports to sponsors and board members.
Updates to museum staff and exhibit curators.
External Communication:
Invitations and updates to guests.
Press releases and marketing materials.
Social media and website updates.
This detailed example provides a comprehensive overview of the various aspects of project management involved in \
sponsoring a new exhibit at a museum. Each aspect, from planning and scheduling to stakeholder management and risk \
assessment, is crucial for the successful execution of the project.
</EXAMPLE>
</CONUNDRUM>
    """
    return prompt_parameter

def get_default_action_plan():
    prompt_parameter = """<ACTION_PLAN>
- Use the content in the CONUNDRUM to provide guidance for completing the task.
- You should limit your responses to topics in the CONUNDRUM

How to Respond:
- If you respond with XML code snippets, use this format "Some Response text ```markdown <TOPIC>My Topic Information</TOPIC>```That is how its done"
- I will be processing your response using the html.escape then markdown2.markdown then html.unescape.

</ACTION_PLAN>"""

    return prompt_parameter