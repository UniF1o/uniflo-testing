"""Fake Wits (PeopleSoft Fluid) portal for adapter testing.

Login flow:
  / → register form (/register-form) → confirm details → email sent → /
  → confirm-password → set-password → password-changed → /
  → sign-in (POST) → /apply-for-admission → /step/1

Wizard steps 1-17 cover all selectors the Wits adapter fills.
"""

from aiohttp import web
from fake_portals._fluid import step_handler

# 1×1 transparent GIF served for decodable captcha images.
_PIXEL_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21,
    0xF9, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3B,
])

# Fake captcha code: images named VC_L_{CHAR}_{n}.JPG → lowercase char
_CAPTCHA_CODE = "abcdef"
_CAPTCHA_IMAGES = [f"VC_L_{c.upper()}_{i+1}.JPG" for i, c in enumerate(_CAPTCHA_CODE)]

# ---------------------------------------------------------------------------
# Login-flow pages
# ---------------------------------------------------------------------------

def _initial_page() -> str:
    return """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Wits Online Application</title></head>
<body>
<h1>Wits Online Application</h1>
<button type="button" id="VC_OA_LOGIN_WRK_REGISTER"
    onclick="location.href='/register-form'">Create Application ID</button>
<button type="button" id="VC_OA_LOGIN_WRK_VC_CONFIRM_PWD_PB"
    onclick="location.href='/confirm-password'">Confirm Temporary Password</button>
<h2>Sign In</h2>
<form action="/sign-in" method="post">
  <p><label>Temporary ID
    <input id="VC_OA_LOGIN_WRK_OPRID" name="oprid" type="text"></label></p>
  <p><label>Password
    <input id="VC_OA_LOGIN_WRK_PASSWORD" name="password" type="password"></label></p>
  <p><input id="VC_OA_LOGIN_WRK_VC_LOGIN_PB" type="submit" value="Sign In"></p>
</form>
</body>
</html>"""


def _register_form() -> str:
    imgs = "".join(
        f'<img alt="Image{i+1}" src="/captcha/{fname}" '
        f'style="width:30px;height:30px">\n'
        for i, fname in enumerate(_CAPTCHA_IMAGES)
    )
    days = "".join(f"<option>{d:02d}</option>" for d in range(1, 32))
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Wits — Create Application ID</title></head>
<body>
<h1>Create Application ID</h1>
<p><label>Nationality
  <select id="VC_OA_LOGIN_WRK_COUNTRY">
    <option>South Africa</option><option>Zimbabwe</option>
  </select></label></p>
<p><label>National ID
  <input id="VC_OA_LOGIN_WRK_NATIONAL_ID" type="text"></label></p>
<p><label>Title
  <select id="VC_OA_LOGIN_WRK_NAME_PREFIX">
    <option>Mr</option><option>Ms</option><option>Mrs</option><option>Dr</option>
  </select></label></p>
<p><label>First Name
  <input id="VC_OA_LOGIN_WRK_FIRST_NAME" type="text"></label></p>
<p><label>Middle Names
  <input id="VC_OA_LOGIN_WRK_MIDDLE_NAME" type="text"></label></p>
<p><label>Last Name
  <input id="VC_OA_LOGIN_WRK_LAST_NAME" type="text"></label></p>
<p><label>Day
  <select id="VC_OA_LOGIN_WRK_CUB_BEGINDAY">{days}</select></label></p>
<p><label>Month
  <select id="VC_OA_LOGIN_WRK_MONTH_XLAT">
    <option>01 - January</option><option>02 - February</option>
    <option>03 - March</option><option>04 - April</option>
    <option>05 - May</option><option>06 - June</option>
    <option>07 - July</option><option>08 - August</option>
    <option>09 - September</option><option>10 - October</option>
    <option>11 - November</option><option>12 - December</option>
  </select></label></p>
<p><label>Year
  <input id="VC_OA_LOGIN_WRK_VC_YEAR" type="text"></label></p>
<p><label>Gender
  <select id="VC_OA_LOGIN_WRK_SEX">
    <option>Male</option><option>Female</option><option>Gender Neutral</option>
  </select></label></p>
<p><label>Email
  <input id="VC_OA_LOGIN_WRK_EMAIL_ADDR" type="email"></label></p>
<p><label>Mobile
  <input id="VC_OA_LOGIN_WRK_VC_PHONE_CELL_SS" type="text"></label></p>
<p>Security code:</p>
{imgs}
<p><label>Security Code
  <input id="VC_OA_LOGIN_WRK_VC_SEC_CODE" type="text"></label></p>
<button type="button" id="VC_OA_LOGIN_WRK_CONTINUE_PB"
    onclick="location.href='/confirm-details'">Continue</button>
</body>
</html>"""


_CONFIRM_DETAILS = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h1>Confirm Application Details</h1>
<p>Please check your details are correct.</p>
<a role="button" onclick="location.href='/email-sent'">Continue</a>
</body>
</html>"""

_EMAIL_SENT = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h1>Confirmation of Email</h1>
<p>Your Temporary Access ID and password have been emailed.</p>
<a role="button" onclick="location.href='/'">OK</a>
</body>
</html>"""

_CONFIRM_PASSWORD = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h1>Confirm Temporary Password</h1>
<p><label>Email
  <input id="VC_OA_LOGIN_WRK_EMAIL_ADDR" type="text"></label></p>
<p><label>Temporary ID
  <input id="VC_OA_LOGIN_WRK_OPRID" type="text"></label></p>
<p><label>Temporary Password
  <input id="VC_OA_LOGIN_WRK_PASSWORD" type="password"></label></p>
<button type="button" id="VC_OA_LOGIN_WRK_CONTINUE_PB"
    onclick="location.href='/set-password'">Continue</button>
</body>
</html>"""

_SET_PASSWORD = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h1>Enter a new password</h1>
<p><label for="new-pwd">Password</label>
  <input id="new-pwd" type="password"></p>
<p><label for="conf-pwd">Confirm Password</label>
  <input id="conf-pwd" type="password"></p>
<a role="button" onclick="location.href='/password-changed'">OK</a>
</body>
</html>"""

_PASSWORD_CHANGED = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h1>Password Changed</h1>
<p>Your password has been successfully changed.</p>
<a role="button" onclick="location.href='/'">OK</a>
</body>
</html>"""

_APPLY_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h1>Apply for Admission</h1>
<p><label for="VC_OA_APPLY_WRK_VC_OA_APPL_ACTN">Action</label>
  <select id="VC_OA_APPLY_WRK_VC_OA_APPL_ACTN">
    <option value="">--</option>
    <option>Begin New Application</option>
    <option>Continue Existing Application</option>
  </select></p>
<p><label for="VC_OA_APPLY_WRK_VC_OA_APP_TYPE">Type</label>
  <select id="VC_OA_APPLY_WRK_VC_OA_APP_TYPE">
    <option value="">--</option>
    <option>Undergraduate Full-Time</option>
    <option>Postgraduate</option>
  </select></p>
<p><label for="VC_OA_APPLY_WRK_ADMIT_TERM">Academic Year</label>
  <select id="VC_OA_APPLY_WRK_ADMIT_TERM">
    <option>2026 Semester 1</option><option>2027 Semester 1</option>
  </select></p>
<p><label for="VC_OA_APPLY_WRK_WITS_ADMISSIONCALE">Calendar</label>
  <select id="VC_OA_APPLY_WRK_WITS_ADMISSIONCALE">
    <option>January</option><option>July</option>
  </select></p>
<a role="button" onclick="location.href='/step/1'">Continue</a>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Modals
# ---------------------------------------------------------------------------

_ADDRESS_MODAL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h3>Address Search Results</h3>
<table>
  <tr>
    <td><button id="VC_OA_WRK_SELECT$0" type="button" onclick="pick()">Select</button></td>
    <td>SOWETO | Johannesburg | 1804 | Gauteng</td>
  </tr>
</table>
<script>
function pick() {
  // Defer removal so the adapter's js_click evaluate (running el.click() in
  // THIS frame) returns before the iframe detaches — mirrors the portal's
  // async AJAX modal close.
  setTimeout(function() {
    try {
      window.parent.document.querySelectorAll('iframe[name^="ptModFrame"]')
          .forEach(function(f) { f.remove(); });
    } catch(e) {}
  }, 50);
}
</script>
</body>
</html>"""

_WITS_UPLOAD_MODAL = """<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body>
<h3>File Attachment</h3>
<input type="file" id="fileInput" style="display:none">
<button type="button" id="PT_ATTACH_BUTTON_DEF"
    onclick="document.getElementById('fileInput').click()">My Device</button>
<button type="button" id="#ICUpload" onclick="showComplete()">Upload</button>
<span id="upload-complete" style="display:none">Upload Complete</span>
<button type="button" id="#ICOK" style="display:none" onclick="closeModal()">Done</button>
<script>
function showComplete() {
  document.getElementById('upload-complete').style.display = '';
  document.getElementById('#ICOK').style.display = '';
}
function closeModal() {
  // Deferred so the adapter's js_click(Done) evaluate returns before the
  // iframe detaches (see the address modal's pick() for the rationale).
  setTimeout(function() {
    try {
      window.parent.document.querySelectorAll('iframe[name^="ptModFrame"]')
          .forEach(function(f) { f.remove(); });
    } catch(e) {}
  }, 50);
}
</script>
</body>
</html>"""

# ---------------------------------------------------------------------------
# Wizard step HTML content
# ---------------------------------------------------------------------------

_SUBJ_OPTS = ("<option value=''>--</option>"
              "<option>Mathematics</option>"
              "<option>English Home Language</option>"
              "<option>Life Orientation</option>"
              "<option>Physical Sciences</option>"
              "<option>Accounting</option>"
              "<option>Geography</option>"
              "<option>History</option>")

_STEPS: list[tuple[int, str, str]] = [
    (1, "Welcome", """
<h2>Welcome to Wits University</h2>
<p>Please read this introduction before proceeding.</p>"""),

    (2, "Personal Details", """
<p><label for="s2-title">Title</label>
  <select id="s2-title">
    <option value="">--</option><option>Mr</option><option>Ms</option>
    <option>Mrs</option><option>Dr</option>
  </select></p>
<p><label for="s2-gender">Gender</label>
  <select id="s2-gender">
    <option value="">--</option><option>Male</option><option>Female</option>
    <option>Gender Neutral</option>
  </select></p>"""),

    (3, "Current Activities", """
<p><label for="VC_OA_STG_GENL_VC_MAIN_ACTIVITY">Activity</label>
  <select id="VC_OA_STG_GENL_VC_MAIN_ACTIVITY">
    <option value="">--</option>
    <option>Completing Matric</option><option>Employed</option>
    <option>Not Employed</option>
  </select></p>
<p><label><input type="checkbox" id="VC_OA_STG_GENL_VC_OA_TERT_FLG">
  Attended a tertiary institution?</label></p>"""),

    (4, "Secondary Education",
     """<p><label>
  <input type="radio" id='VC_OA_STG_SEDH_VC_OA_SCHL_TYPE$1' name="school_status">
  Completed Grd 12 OR Upgrading
</label></p>
<button id="Select School" type="button">Select School</button>
<p><label for="VC_OA_STG_SEDH_WITS_EXM_AUT_CD">Examining Authority</label>
  <select id="VC_OA_STG_SEDH_WITS_EXM_AUT_CD">
    <option value="">--</option>
    <option>DBE (NSC)</option><option>IEB</option><option>International</option>
  </select></p>
<p><label>Exam Year
  <input id="VC_OA_STG_SEDH_VC_FINAL_SCHL_YEAR" type="text"></label></p>
<p><label for="VC_OA_STG_SEDH_UW_EXAM_MONTH">Exam Month</label>
  <select id="VC_OA_STG_SEDH_UW_EXAM_MONTH">
    <option value="">--</option>
    <option>November</option><option>June</option><option>March</option>
  </select></p>
<p><label>Exam Number
  <input id="VC_OA_STG_SEDH_WITS_EXAMNUM" type="text"></label></p>
<h3>Grade 11 Subjects</h3>
""" + "".join(
         f"<p><label for='VC_OA_STG_SEDG_SCHOOL_CRSE_NBR${n}'>Subject {n+1}</label>"
         f"<select id='VC_OA_STG_SEDG_SCHOOL_CRSE_NBR${n}'>{_SUBJ_OPTS}</select>"
         f"<label>Mark <input id='VC_OA_STG_SEDG_VC_GRADE${n}' type='text' "
         f"style='width:4em'></label></p>"
         for n in range(7)
     ) + """
<button id="VC_OA_WRK_VC_COPY_GR11_SUBJ" type="button">Copy Gr11 Subjects</button>"""),

    (5, "Tertiary Education", """
<p><label><input type="checkbox" id="VC_OA_STG_GENL_VC_OA_TERT_FLG">
  Previously enrolled at a tertiary institution?</label></p>"""),

    (6, "Study Choices",
     "<p>Select your programme preferences.</p>"
     + "".join(
         f"<p>"
         f"<label for='VC_OA_WRK_VC_ACAD_PROG{n}'>Programme {n}</label>"
         f"<select id='VC_OA_WRK_VC_ACAD_PROG{n}'>"
         f"<option value=''>--</option>"
         f"<option>Computer Science</option>"
         f"<option>Electrical Engineering</option>"
         f"<option>Information Systems</option>"
         f"</select>"
         f"<label for='VC_OA_WRK_VC_ACAD_PLAN{n}'>Plan {n}</label>"
         f"<select id='VC_OA_WRK_VC_ACAD_PLAN{n}'>"
         f"<option value=''>--</option>"
         f"<option>BSc Computer Science</option>"
         f"<option>BSc Information Technology</option>"
         f"</select></p>"
         for n in range(1, 4)
     )
     + """<a role="button" onclick="void(0)">Validate Application</a>"""),

    (7, "Domicilium Address", """
<p><label>Address Line 1
  <input id="VC_OA_STG_ADD1_ADDRESS1" type="text"></label></p>
<p><label>Address Line 2
  <input id="VC_OA_STG_ADD1_ADDRESS2" type="text"></label></p>
<p><label>Suburb
  <input id="VC_OA_STG_ADD1_ADDRESS3" type="text"></label></p>
<button type="button" id="VC_OA_WRK_ADDRESS_LOOKUP" onclick="openAddressModal()">
  Address Search</button>
<script>
function openAddressModal() {
  var existing = document.querySelector('iframe[name^="ptModFrame"]');
  if (existing) existing.remove();
  var f = document.createElement('iframe');
  f.name = 'ptModFrame_0'; f.src = '/modal/address';
  f.style.cssText = 'position:fixed;top:50px;left:50px;width:600px;height:300px;' +
    'z-index:9999;background:white;border:2px solid #333';
  document.body.appendChild(f);
}
</script>"""),

    (8, "Residential Address", """
<p><label for="VC_OA_STG_ADD2_VC_USE_ADDRESS">Same as</label>
  <select id="VC_OA_STG_ADD2_VC_USE_ADDRESS">
    <option value="">--</option><option>Domicilium</option>
  </select></p>"""),

    (9, "Postal Address", """
<p><label for="VC_OA_STG_ADD3_VC_USE_ADDRESS">Same as</label>
  <select id="VC_OA_STG_ADD3_VC_USE_ADDRESS">
    <option value="">--</option><option>Domicilium</option>
  </select></p>"""),

    (10, "Contact Details", """
<p><label>Mobile
  <input id="VC_OA_STG_CNTC_VC_PHONE_CELL_SS" type="text"></label></p>"""),

    (11, "Demographic Details", """
<p><label for="VC_OA_STG_DEMO_MAR_STATUS">Marital Status</label>
  <select id="VC_OA_STG_DEMO_MAR_STATUS">
    <option value="">--</option>
    <option>Single</option><option>Married</option><option>Other</option>
  </select></p>
<p><label for="VC_OA_STG_DEMO_ETHNIC_GRP_CD">Population Group</label>
  <select id="VC_OA_STG_DEMO_ETHNIC_GRP_CD">
    <option value="">--</option>
    <option>Black</option><option>Coloured</option>
    <option>Indian</option><option>White</option>
  </select></p>
<p><label for="VC_OA_STG_DEMO_LANG_CD">Home Language</label>
  <select id="VC_OA_STG_DEMO_LANG_CD">
    <option value="">--</option>
    <option>English</option><option>Afrikaans</option><option>isiZulu</option>
  </select></p>
<p><label for="VC_OA_STG_DEMO_RELIGIOUS_PREF">Religion</label>
  <select id="VC_OA_STG_DEMO_RELIGIOUS_PREF">
    <option value="">--</option>
    <option>Nil Declared</option><option>Christian</option><option>Muslim</option>
  </select></p>
<p><label for="VC_OA_STG_DEMO_DISABLED">Disability</label>
  <select id="VC_OA_STG_DEMO_DISABLED">
    <option value="">--</option>
    <option>No</option><option>Yes</option>
  </select></p>"""),

    (12, "Next of Kin", """
<p><label for="VC_OA_STG_NKIN_NAME_PREFIX">NOK Title</label>
  <select id="VC_OA_STG_NKIN_NAME_PREFIX">
    <option value="">--</option><option>Mr</option><option>Ms</option><option>Mrs</option>
  </select></p>
<p><label>NOK Initial
  <input id="VC_OA_STG_NKIN_FIRST_NAME" type="text"></label></p>
<p><label>NOK Surname
  <input id="VC_OA_STG_NKIN_LAST_NAME" type="text"></label></p>
<p><label>NOK Mobile
  <input id="VC_OA_STG_NKIN_VC_PHONE_CELL_SS" type="text"></label></p>
<p><label for="VC_OA_STG_NKIN_PEOPLE_RELATION">Relationship</label>
  <select id="VC_OA_STG_NKIN_PEOPLE_RELATION">
    <option value="">--</option>
    <option>Parent</option><option>Guardian</option><option>Sibling</option>
  </select></p>
<p><label>NOK Email
  <input id="VC_OA_STG_NKIN_EMAIL_ADDR" type="email"></label></p>
<p><label for="VC_OA_STG_NKIN_VC_USE_ADDRESS">NOK Address Same As</label>
  <select id="VC_OA_STG_NKIN_VC_USE_ADDRESS">
    <option value="">--</option><option>Domicilium</option>
  </select></p>"""),

    (13, "Emergency Contact", """
<p><label><input type="checkbox" id="VC_OA_STG_GENL_VC_OA_EMERG_FLG">
  Use same details as Next of Kin?</label></p>
<p><label for="VC_OA_STG_EMER_RELATIONSHIP">Relationship</label>
  <select id="VC_OA_STG_EMER_RELATIONSHIP">
    <option value="">--</option>
    <option>Parent</option><option>Guardian</option><option>Sibling</option>
  </select></p>"""),

    (14, "Indemnity", """
<p>Indemnity &amp; Undertaking</p>
<p>Indemnity and Undertaking Complete</p>
<button type="button" id="SCC_TM_ADM_WRK_SCC_TM_ACCEPT">I Accept</button>"""),

    (15, "Payment", "<p>Payment information (R100 application fee).</p>"),

    (16, "Documents", """<p>Documents</p>
<a id='VC_OA_WRK_FILE_CREATE1_LBL$0' onclick="openUploadModal(0)"
   style="cursor:pointer;text-decoration:underline">Add ID Copy</a>
<a id='VC_OA_WRK_FILE_CREATE1_LBL$1' onclick="openUploadModal(1)"
   style="cursor:pointer;text-decoration:underline">Add Grade 11 Results</a>
<script>
function openUploadModal(n) {
  var existing = document.querySelector('iframe[name^="ptModFrame"]');
  if (existing) existing.remove();
  var f = document.createElement('iframe');
  f.name = 'ptModFrame_' + n; f.src = '/modal/upload-wits';
  f.style.cssText = 'position:fixed;top:50px;left:50px;width:500px;height:300px;' +
    'z-index:9999;background:white;border:2px solid #333';
  document.body.appendChild(f);
}
</script>"""),

    (17, "Submit", "<p>Review and submit your application.</p>"),
]


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def make_wits_app() -> web.Application:
    app = web.Application()

    def html_handler(html: str):
        async def h(r: web.Request) -> web.Response:
            return web.Response(text=html, content_type="text/html")
        return h

    async def captcha_img(r: web.Request) -> web.Response:
        return web.Response(body=_PIXEL_GIF, content_type="image/gif")

    async def sign_in_post(r: web.Request) -> web.Response:
        raise web.HTTPFound("/apply-for-admission")

    async def complete(r: web.Request) -> web.Response:
        html = "<html><body><h1>Application submitted (TEST MODE)</h1></body></html>"
        return web.Response(text=html, content_type="text/html")

    app.router.add_get("/", html_handler(_initial_page()))
    app.router.add_get("/register-form", html_handler(_register_form()))
    app.router.add_get("/confirm-details", html_handler(_CONFIRM_DETAILS))
    app.router.add_get("/email-sent", html_handler(_EMAIL_SENT))
    app.router.add_get("/confirm-password", html_handler(_CONFIRM_PASSWORD))
    app.router.add_get("/set-password", html_handler(_SET_PASSWORD))
    app.router.add_get("/password-changed", html_handler(_PASSWORD_CHANGED))
    app.router.add_get("/apply-for-admission", html_handler(_APPLY_HTML))
    app.router.add_post("/sign-in", sign_in_post)
    app.router.add_get("/captcha/{filename}", captcha_img)
    app.router.add_get("/modal/address", html_handler(_ADDRESS_MODAL))
    app.router.add_get("/modal/upload-wits", html_handler(_WITS_UPLOAD_MODAL))
    app.router.add_get("/complete", complete)

    # Info-only steps the adapter advances with a direct Next (no Save first),
    # so their Next must be visible on load: 1 (Welcome), 14 (Indemnity),
    # 15 (Payment).
    _INFO_ONLY_STEPS = {1, 14, 15}
    for n, title, fields in _STEPS:
        next_url = f"/step/{n+1}" if n < 17 else "/complete"
        app.router.add_get(
            f"/step/{n}",
            step_handler(n, title, fields, next_url, info_only=(n in _INFO_ONLY_STEPS)),
        )

    return app
