"""Fake UCT (PeopleSoft Fluid) portal for adapter testing.

Login flow:
  LOGIN_URL → login form (userid/pwd) → homepage with "Online Application Homepage"
  text → "Undergraduate" button → start page → alert dialog "Yes" → Step 1

Wizard steps 1-16 are served; each has the field IDs the UCT adapter expects.
Steps with only Save/Next (adapter fills nothing else) serve just those buttons.

upload_documents (step 14) requires a dummy SA-ID document file — the test
fixture supplies one via DocumentRef.
"""

from aiohttp import web
from fake_portals._fluid import step_handler, upload_modal_html

# ---------------------------------------------------------------------------
# Login / homepage / application-start pages
# ---------------------------------------------------------------------------

_LOGIN_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>UCT Online Application Login</title></head>
<body>
<h1>UCT Online Application</h1>
<form action="/login" method="post">
  <p>
    <label>User ID <input id="userid" name="userid" type="text"></label>
  </p>
  <p>
    <label>Password <input id="pwd" name="pwd" type="password"></label>
  </p>
  <p><input id="login" type="submit" value="Sign In"></p>
</form>
</body>
</html>"""

# _on_homepage checks body.innerText.includes('Online Application Homepage')
_HOMEPAGE_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>UCT Online Application Homepage</title></head>
<body>
<h1>Online Application Homepage</h1>
<p>Welcome to the UCT Online Application system.</p>
<!-- adapter: page.get_by_label("Undergraduate").get_by_role("button").click()
     needs a container element with aria-label="Undergraduate" containing a button -->
<div aria-label="Undergraduate">
  <button onclick="location.href='/start'">Start Application</button>
</div>
</body>
</html>"""

# _enter_application: clicks "Start Application" → alert confirm → wizard
_START_HTML = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>UCT — Start Application</title></head>
<body>
<h1>New Undergraduate Application</h1>
<div role="alertdialog" id="confirm-dlg" style="display:none;border:2px solid red;padding:12px">
  Your application will be created. Continue?
  <button onclick="document.getElementById('confirm-dlg').style.display='none';
                  location.href='/step/2'">Yes</button>
  <button onclick="document.getElementById('confirm-dlg').style.display='none'">No</button>
</div>
<script>
function startApp() {
  // fluid.answer_alert looks for [role=alertdialog] in the DOM
  document.getElementById('confirm-dlg').style.display = '';
}
</script>
<a role="button" onclick="startApp()">Start Application</a>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Wizard steps HTML content
# ---------------------------------------------------------------------------

# Step 1: info-only — adapter checks for "Next" button and clicks it
_STEP1_FIELDS = "<p>Introduction: please read the instructions before proceeding.</p>"

# Step 2: Personal Information
# _select_by_label_text finds <select> whose labels[0].textContent matches
# the label argument. The label text must match EXACTLY.
_STEP2_FIELDS = """
<p>
  <label for="s2-title">Title</label>
  <select id="s2-title">
    <option value="">--</option><option>Mr</option><option>Ms</option>
    <option>Mrs</option><option>Dr</option><option>Prof</option>
  </select>
</p>
<p>
  <label for="s2-sex">*Sex</label>
  <select id="s2-sex">
    <option value="">--</option><option>Male</option><option>Female</option>
  </select>
</p>
<p>
  <label for="s2-lang">*Home Language</label>
  <select id="s2-lang">
    <option value="">--</option>
    <option>English</option><option>Afrikaans</option><option>isiZulu</option>
    <option>isiXhosa</option><option>Sesotho</option><option>Other</option>
  </select>
</p>
<p>
  <label for="s2-citz">*Indicate Type of Citizenship or Residency in SA</label>
  <select id="s2-citz">
    <option value="">--</option>
    <option>SA Citizen</option>
    <option>Permanent Resident</option>
    <option>Foreign National</option>
  </select>
</p>
<p>
  <label for="s2-race">*Race</label>
  <select id="s2-race">
    <option value="">--</option>
    <option>African</option><option>Coloured</option>
    <option>Indian/Asian</option><option>White</option>
    <option>Prefer not to say</option>
  </select>
</p>
<p>
  <label for="s2-id">*SA ID Number</label>
  <input id="s2-id" type="text">
</p>"""

# Step 3: Contact Details
_STEP3_FIELDS = """
<p>
  <label for="s3-postal">*Postal Code</label>
  <input id="s3-postal" type="text">
</p>
<p>
  <label for="UCT_OA_CONTACT_UCT_SA_CITY4">Suburb</label>
  <select id="UCT_OA_CONTACT_UCT_SA_CITY4">
    <option value="">--</option>
    <option>Soweto</option><option>Sandton</option>
    <option>Rosebank</option><option>Braamfontein</option>
  </select>
</p>
<p>
  <label for="UCT_OA_CONTACT_ADDRESS1">Street Address</label>
  <input id="UCT_OA_CONTACT_ADDRESS1" type="text">
</p>
<script>
function openPhoneModal() {
  var iframe = document.createElement('iframe');
  iframe.name = 'ptModFrame_0';
  iframe.src = '/modal/phone';
  iframe.style.cssText = 'position:fixed;top:50px;left:50px;width:380px;height:200px;z-index:9999;background:white;border:2px solid #333';
  document.body.appendChild(iframe);
}
</script>
<p>
  <button type="button" onclick="openPhoneModal()">Add Contact Number</button>
</p>"""

_PHONE_MODAL_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head><body>
<h3>Add Phone Number</h3>
<p>
  <label for="pm-type">Phone Type</label>
  <select id="pm-type">
    <option value=""></option>
    <option>SA Cellular</option>
    <option>Home</option>
    <option>Work</option>
  </select>
</p>
<p>
  <label for="pm-tel">Telephone</label>
  <input type="text" id="pm-tel">
</p>
<button type="button" onclick="
  window.parent.document.querySelectorAll('iframe[name^=ptModFrame]').forEach(function(f){f.remove();});
">Save</button>
</body></html>"""

# Step 4: Parent/Guardian — all adapter fills are optional (if value:)
_STEP4_FIELDS = """
<p>
  <label for="UCT_OA_PARENT_UCT_TITLE_GUARDIAN">Title</label>
  <select id="UCT_OA_PARENT_UCT_TITLE_GUARDIAN">
    <option value="">--</option><option>Mr</option><option>Ms</option><option>Mrs</option>
  </select>
</p>
<p><label>First Name<input id="UCT_OA_PARENT_UCT_FIRST_NAME_GUA" type="text"></label></p>
<p><label>Last Name<input id="UCT_OA_PARENT_UCT_LAST_NAME_GUAR" type="text"></label></p>
<p><label>ID Number<input id="UCT_OA_PARENT_UCT_NATIONAL_ID_GU" type="text"></label></p>
<p><label>Email<input id="UCT_OA_PARENT_EMAIL_ADDR" type="text"></label></p>
<p><label>Phone<input id="UCT_OA_PARENT_PHONE_DAY" type="text"></label></p>
<p>
  <label for="UCT_OA_PARENT_PEOPLE_RELATION">Relationship</label>
  <select id="UCT_OA_PARENT_PEOPLE_RELATION">
    <option value="">--</option>
    <option>Parent</option><option>Guardian</option><option>Sibling</option>
  </select>
</p>
<p>
  <label>
    <input type="checkbox" id="UCT_OA_PARENT_UCT_GUARDIAN_PAYER">
    Guardian is fee payer
  </label>
</p>"""

# Step 5: Secondary School Information
_STEP5_FIELDS = """
<p>
  <label for="UCT_OA_SCHOOL_UCT_YEAR_CODE">Matric Year</label>
  <select id="UCT_OA_SCHOOL_UCT_YEAR_CODE">
    <option value="">--</option>
    <option>2024</option><option>2023</option><option>2022</option>
  </select>
</p>
<p>
  <label for="UCT_OA_SCHOOL_TRNSCRPT_STATUS">Transcript</label>
  <select id="UCT_OA_SCHOOL_TRNSCRPT_STATUS">
    <option value="">--</option>
    <option>4 Terms</option><option>2 Terms</option><option>Full Year</option>
  </select>
</p>
<p>
  <label for="UCT_OA_SCHOOL_UCT_SCHOOL_AUTH">Qualification</label>
  <select id="UCT_OA_SCHOOL_UCT_SCHOOL_AUTH">
    <option value="">--</option>
    <option>NSC(DBE, IEB or SACAI)</option>
    <option>IEB</option><option>International</option>
  </select>
</p>
<p>
  <button id="PTS_SRCH_BTN" type="button">Search School</button>
</p>
<p>
  <!-- grade radio: _fill_grade12_april clicks this before filling gr12 subjects -->
  <input type="radio" id="UCT_DERIVED_ONL_UCT_SCHOOL_GRADE$105$" name="grade-view" value="12">
  <label for="UCT_DERIVED_ONL_UCT_SCHOOL_GRADE$105$">Grade 12 view</label>
</p>
<script>
function openSubjectModal(src) {
  document.querySelectorAll('iframe[name^="ptModFrame"]').forEach(function(f){f.remove();});
  var iframe = document.createElement('iframe');
  iframe.name = 'ptModFrame_0';
  iframe.src = src;
  iframe.style.cssText = 'position:fixed;top:50px;left:50px;width:420px;height:260px;z-index:9999;background:white;border:2px solid #333';
  document.body.appendChild(iframe);
}
</script>
<h3>Grade 11 Subjects</h3>
""" + "\n".join(
    f'<button id="UCT_SCHLCRSE_H1$0_row_{n}" type="button" '
    f'onclick="openSubjectModal(\'/modal/subject-gr11\')">Add Gr11 Subject {n+1}</button>'
    for n in range(7)
) + """
<h3>Grade 12 April Subjects</h3>
""" + "\n".join(
    f'<button id="UCT_SCHLCRSE_H11$0_row_{n}" type="button" '
    f'onclick="openSubjectModal(\'/modal/subject-gr12\')">Add Gr12 Subject {n+1}</button>'
    for n in range(7)
)

# Step 6: Tertiary Information — set_switch on a checkbox
_STEP6_FIELDS = """
<p>
  <label>
    <input type="checkbox" id="UCT_OA_TERTIARY_UCT_TERTIARY_INDIC">
    Applied to another tertiary institution?
  </label>
</p>"""

# Step 7: Post-school — just Save/Next
_STEP7_FIELDS = "<p>Post-school activity information.</p>"

# Step 8: Programme Choices — cascade selects
# adapter: career → read faculties → set faculty → read progs → match → set → read plans → set
_STEP8_FIELDS = """
<p>
  <label for="UCT_OA_CHOICE_ACAD_CAREER">Level</label>
  <select id="UCT_OA_CHOICE_ACAD_CAREER">
    <option value="">--</option><option>Undergraduate</option><option>Postgraduate</option>
  </select>
</p>
<p>
  <label for="UCT_OA_CHOICE_ACAD_GROUP">Faculty</label>
  <select id="UCT_OA_CHOICE_ACAD_GROUP">
    <option value="">--</option>
    <option>Engineering &amp; the Built Environment</option>
    <option>Science</option>
    <option>Humanities</option>
    <option>Commerce</option>
  </select>
</p>
<p>
  <label for="UCT_OA_CHOICE_ACAD_PROG">Qualification</label>
  <select id="UCT_OA_CHOICE_ACAD_PROG">
    <option value="">--</option>
    <option>Computer Science</option>
    <option>Electrical Engineering</option>
    <option>Mechanical Engineering</option>
    <option>Information Systems</option>
  </select>
</p>
<p>
  <label for="UCT_OA_CHOICE_ACAD_PLAN">Specialisation</label>
  <select id="UCT_OA_CHOICE_ACAD_PLAN">
    <option value="">--</option>
    <option>Computer Science (BSc)</option>
    <option>Information Technology</option>
  </select>
</p>"""

# Step 9: Referees — just Save/Next
_STEP9_FIELDS = "<p>Referee information (not required for undergraduate).</p>"

# Step 10: NBT Information
_STEP10_FIELDS = """
<p><label>NBT Reg Number<input id="UCT_ONL_APP_NBT_UCT_NBT_REG_NUMBER" type="text"></label></p>
<p>
  <label for="UCT_ONL_APP_NBT_UCT_NBT_REG_YEAR">NBT Year</label>
  <select id="UCT_ONL_APP_NBT_UCT_NBT_REG_YEAR">
    <option value="">--</option>
    <option>2025</option><option>2024</option><option>2026</option>
  </select>
</p>
<p>
  <label for="UCT_ONL_APP_NBT_UCT_NBT_DATE">NBT Date</label>
  <select id="UCT_ONL_APP_NBT_UCT_NBT_DATE">
    <option value="">--</option>
    <option>2025-09-01</option>
    <option>2025-06-15</option>
    <option>2025-03-10</option>
  </select>
</p>"""

# Step 11: Funding Information — two switches
_STEP11_FIELDS = """
<p><label>
  <input type="checkbox" id="UCT_ONL_APP_FND_UCT_OA_FUND_OTHER">
  NSFAS at another institution?
</label></p>
<p><label>
  <input type="checkbox" id="UCT_ONL_APP_FND_UCT_OA_FUND_AID">
  Need financial assistance?
</label></p>"""

# Step 12: Housing — one switch
_STEP12_FIELDS = """
<p><label>
  <input type="checkbox" id="UCT_ONL_APP_HSE_UCT_SF_HOUSING">
  Apply for housing?
</label></p>"""

# Step 13: Redress — 8 dropdowns, each must have "I choose not to answer"
_REDRESS_IDS = [
    "UCT_OA_REDRESS_UCT_ETHNIC_MOTHER",
    "UCT_OA_REDRESS_UCT_ETHNIC_FATHER",
    "UCT_OA_REDRESS_UCT_PRM_GUARD_LANG",
    "UCT_OA_REDRESS_UCT_MOM_UNIV_DGREE",
    "UCT_OA_REDRESS_UCT_DAD_UNIV_DGREE",
    "UCT_OA_REDRESS_UCT_GRAN_UNIV_DGRE",
    "UCT_OA_REDRESS_UCT_CHILD_SUPPORT",
    "UCT_OA_REDRESS_UCT_SUPPT_PENSION",
]
_STEP13_FIELDS = "".join(
    f"""<p><label for="{rid}">{rid.split("UCT_OA_REDRESS_UCT_")[1]}</label>
  <select id="{rid}">
    <option value="">--</option>
    <option>I choose not to answer</option>
    <option>African/Black</option><option>Coloured</option>
    <option>Indian/Asian</option><option>White</option>
    <option>I do not know</option>
  </select></p>"""
    for rid in _REDRESS_IDS
)

# Step 14: Document Uploads — the complex upload modal
# Clicking #SCC_ATCH_WRK_ATTACHADD$0 should inject an iframe named ptModFrame_0
_STEP14_FIELDS = """
<p>Please attach your Identity Document.</p>
<button id="SCC_ATCH_WRK_ATTACHADD$0" type="button" onclick="openUploadModal()">
  Add Attachment
</button>
<div id="upload-status"></div>
<script>
function openUploadModal() {
  var iframe = document.createElement('iframe');
  iframe.name = 'ptModFrame_0';
  iframe.src = '/modal/upload';
  iframe.style.cssText = [
    'position:fixed', 'top:50px', 'left:50px',
    'width:500px', 'height:300px', 'z-index:9999',
    'background:white', 'border:2px solid #333'
  ].join(';');
  document.body.appendChild(iframe);
}
</script>"""

# Steps 15/16 are only reached by submit() — not tested (allow_submit=False)
_STEP15_FIELDS = "<p>Review your application.</p>"
_STEP16_FIELDS = "<p>Submit your application.</p>"

# ---------------------------------------------------------------------------
# Step configs: (step_n, title, fields_html, next_url)
# ---------------------------------------------------------------------------

_STEPS = [
    (1,  "Introduction",                  _STEP1_FIELDS,  "/step/2"),
    (2,  "Personal Information",           _STEP2_FIELDS,  "/step/3"),
    (3,  "Contact Details",                _STEP3_FIELDS,  "/step/4"),
    (4,  "Parent/Guardian and Fee Payer",  _STEP4_FIELDS,  "/step/5"),
    (5,  "Secondary School Information",   _STEP5_FIELDS,  "/step/6"),
    (6,  "Tertiary Information",           _STEP6_FIELDS,  "/step/7"),
    (7,  "Post School Activity",           _STEP7_FIELDS,  "/step/8"),
    (8,  "Programme Choices",              _STEP8_FIELDS,  "/step/9"),
    (9,  "Referees & Supervisors",         _STEP9_FIELDS,  "/step/10"),
    (10, "NBT Information",                _STEP10_FIELDS, "/step/11"),
    (11, "Funding Information",            _STEP11_FIELDS, "/step/12"),
    (12, "Housing Information",            _STEP12_FIELDS, "/step/13"),
    (13, "Redress and Disadvantage",       _STEP13_FIELDS, "/step/14"),
    (14, "Document Uploads",               _STEP14_FIELDS, "/step/15"),
    (15, "Review",                         _STEP15_FIELDS, "/step/16"),
    (16, "Submit",                         _STEP16_FIELDS, "/complete"),
]


_SUBJECT_MODAL_CLOSE_JS = """<script>
function closeModal() {
  // Defer removal so the adapter's js_click evaluate (which runs el.click()
  // synchronously in THIS frame) can return before the iframe detaches —
  // mirrors the real portal's async AJAX modal close.
  setTimeout(function() {
    try {
      window.parent.document.querySelectorAll('iframe[name^="ptModFrame"]')
        .forEach(function(f){f.remove();});
    } catch(e){}
  }, 50);
}
</script>"""

_SUBJECT_GR11_MODAL_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head><body>
<h3>Grade 11 Subject</h3>
<p>
  <label for="gr11-subj">Subject Name</label>
  <select id="gr11-subj">
    <option value=""></option>
    <option>Mathematics</option>
    <option>English Home Language</option>
    <option>Life Orientation</option>
    <option>Physical Sciences</option>
    <option>Accounting</option>
    <option>Geography</option>
    <option>History</option>
    <option>Afrikaans First Additional Language</option>
    <option>Economics</option>
    <option>Business Studies</option>
  </select>
</p>
<p>
  <label for="gr11-pct">Mark %</label>
  <input type="text" id="gr11-pct">
</p>
<button id="UCT_DERIVED_ONL_CONFIRM_PB" type="button" onclick="closeModal()">OK</button>
""" + _SUBJECT_MODAL_CLOSE_JS + "</body></html>"

_SUBJECT_GR12_MODAL_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head><body>
<h3>Grade 12 Subject</h3>
<p><label for="UCT_OA_COURSES_CRSE_GRADE_INPUT1">April Grade</label>
   <input type="text" id="UCT_OA_COURSES_CRSE_GRADE_INPUT1"></p>
<button id="UCT_DERIVED_ONL_CONFIRM_PB" type="button" onclick="closeModal()">OK</button>
""" + _SUBJECT_MODAL_CLOSE_JS + "</body></html>"


async def handle_complete(request: web.Request) -> web.Response:
    html = """<!DOCTYPE html><html><body>
<h1>Application Submitted (TEST MODE)</h1>
<p>Your application has been submitted. Applicant number: TEST-12345</p>
</body></html>"""
    return web.Response(text=html, content_type="text/html")


async def handle_upload_modal(request: web.Request) -> web.Response:
    return web.Response(text=upload_modal_html(), content_type="text/html")


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def make_uct_app() -> web.Application:
    app = web.Application()

    async def login_get(r: web.Request) -> web.Response:
        return web.Response(text=_LOGIN_HTML, content_type="text/html")

    async def login_post(r: web.Request) -> web.Response:
        raise web.HTTPFound("/homepage")

    async def homepage(r: web.Request) -> web.Response:
        return web.Response(text=_HOMEPAGE_HTML, content_type="text/html")

    async def start_get(r: web.Request) -> web.Response:
        return web.Response(text=_START_HTML, content_type="text/html")

    async def subject_gr11_modal(r: web.Request) -> web.Response:
        return web.Response(text=_SUBJECT_GR11_MODAL_HTML, content_type="text/html")

    async def subject_gr12_modal(r: web.Request) -> web.Response:
        return web.Response(text=_SUBJECT_GR12_MODAL_HTML, content_type="text/html")

    async def phone_modal(r: web.Request) -> web.Response:
        return web.Response(text=_PHONE_MODAL_HTML, content_type="text/html")

    app.router.add_get("/login", login_get)
    app.router.add_post("/login", login_post)
    app.router.add_get("/homepage", homepage)
    app.router.add_get("/start", start_get)
    app.router.add_get("/modal/upload", handle_upload_modal)
    app.router.add_get("/modal/subject-gr11", subject_gr11_modal)
    app.router.add_get("/modal/subject-gr12", subject_gr12_modal)
    app.router.add_get("/modal/phone", phone_modal)
    app.router.add_get("/complete", handle_complete)

    for step_n, title, fields, next_url in _STEPS:
        app.router.add_get(f"/step/{step_n}", step_handler(step_n, title, fields, next_url))

    return app
