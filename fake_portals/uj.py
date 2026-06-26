"""Fake UJ (ITS Integrator) portal for adapter testing.

Serves all 7 pages of the UJ online application form plus LOV popup pages.
HTML has the exact element IDs the UJAdapter expects; form POSTs redirect to
the next page; LOV popups set the parent-window field value and close.

No credentials are validated — any input is accepted.
No data is stored — state lives only in the browser session.
"""

import json
from aiohttp import web

# ---------------------------------------------------------------------------
# LOV option data (values the fake LOVs will serve)
# ---------------------------------------------------------------------------

_LOV: dict[str, list[str]] = {
    # Standard LOVs (link text = the value set in the parent field)
    "oapCitzCode": ["South Africa", "Zimbabwe", "Botswana", "Namibia"],
    "oapStreetAddrPCodeRq": ["1804", "2000", "0001", "4001", "7700"],
    "oapAcntPostalCode": ["1804", "2000", "0001", "4001", "7700"],
    "oapMGrade": ["NSC", "IEB", "SACAI"],
    "oapsymbGr11": [str(i) for i in range(30, 100)],
    "oapPact": ["GRADE 12 PUPIL", "EMPLOYED", "UNEMPLOYED", "NOT EMPLOYED"],
    "oapStudyPeriod": ["FIRST YEAR", "SECOND YEAR", "THIRD YEAR"],
    "oapOfferingType": ["APK CAMPUS FULL-TIME", "DFC CAMPUS FULL-TIME"],
    "oapMatType": ["CURRENTLY IN GR.12", "COMPLETED GR.12", "CURRENTLY IN GR.11"],
    # Subject LOV — qualified ITS names that best_subject_match will recognise.
    # Use full words (not abbreviations) so token matching works.
    "oapMSubj": [
        "MATHEMATICS (NSC/NCV/ISC)",
        "ENGLISH HOME LANGUAGE (NSC/NCV)",
        "ENGLISH FIRST ADDITIONAL LANGUAGE (NSC/NCV)",
        "LIFE ORIENTATION (NSC/NCV/DR)",
        "PHYSICAL SCIENCES (NSC/NCV/ISC)",
        "ACCOUNTING (NSC/NCV/ISC)",
        "GEOGRAPHY (NSC/NCV/ISC)",
        "HISTORY (NSC/NCV/ISC)",
        "AFRIKAANS HOME LANGUAGE (NSC/NCV)",
        "MATHEMATICAL LITERACY (NSC/NCV)",
    ],
    # School LOV — searched by school name
    "oapSchool": [
        "SOWETO SECONDARY SCHOOL",
        "ORLANDO EAST SECONDARY",
        "JOHANNESBURG HIGH SCHOOL",
    ],
    # Faculty LOV — searched by abbreviated name
    "oapFaculty": [
        "ENGINEERING&BUILT ENVIRONMENT",
        "HUMANITIES",
        "SCIENCE",
        "LAW",
        "MANAGEMENT",
        "HEALTH SCIENCES",
    ],
    # Study period (also used by _E_STUDY_PERIOD)
    "oapStudyPeriod_": ["FIRST YEAR", "SECOND YEAR"],
}

# Programme LOV uses a two-column table (code + description); adapter's
# best_programme_match needs "(ELIGIBLE TO APPLY-Y)" in the row text.
_PROGRAMME_ROWS = [
    ("BCSQ01", "(ELIGIBLE TO APPLY-Y) - Bachelor of Science Computer Science"),
    ("BEEQ01", "(ELIGIBLE TO APPLY-Y) - BEng Electrical Engineering"),
    ("BMGQ01", "(ELIGIBLE TO APPLY-Y) - Bachelor of Commerce Management"),
    ("BCEQ01", "(ELIGIBLE TO APPLY-N) - BEng Civil Engineering"),
]


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def _page(title: str, body: str) -> web.Response:
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{title}</title></head>
<body>
<h1>{title}</h1>
{body}
</body>
</html>"""
    return web.Response(text=html, content_type="text/html")


def _select(id_: str, name: str, options: list[tuple[str, str]], required: bool = False) -> str:
    """Render a <select> with value/label option pairs."""
    opts = '<option value="">--Select--</option>'
    for val, label in options:
        opts += f'<option value="{val}">{label}</option>'
    req = 'required' if required else ''
    return f'<select id="{id_}" name="{name}" {req}>{opts}</select>'


def _text(id_: str, name: str = "", readonly: bool = False) -> str:
    ro = "readonly" if readonly else ""
    n = name or id_
    return f'<input type="text" id="{id_}" name="{n}" {ro}>'


def _lov_trigger(field_id: str, label: str = "Select") -> str:
    """Hidden text input (set by LOV) + anchor that opens the LOV popup."""
    return (
        f'<input type="text" id="{field_id}" name="{field_id}" readonly style="width:200px">'
        f'<a href="/lov/{field_id}" target="_blank" style="margin-left:4px">[{label}]</a>'
    )


def _lov_popup_html(field_id: str, options: list[str]) -> str:
    """LOV popup page with search box + clickable result links.

    On click the result link:
      1. Sets window.opener's field to the chosen value
      2. Fires a change event
      3. Closes this popup
    """
    opts_json = json.dumps(options)
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Select</title></head>
<body>
<div>
  <input type="text" name="x_thefilter" placeholder="Filter..." style="width:200px">
  <button type="button">Search</button>
</div>
<div id="results"></div>
<script>
const FIELD_ID = {json.dumps(field_id)};
const ALL_OPTIONS = {opts_json};

function pick(value) {{
  try {{
    var opener = window.opener;
    if (opener) {{
      var el = opener.document.querySelector('#' + FIELD_ID);
      if (el) {{
        el.value = value;
        el.dispatchEvent(new Event('change', {{bubbles: true}}));
        el.dispatchEvent(new Event('blur', {{bubbles: true}}));
      }}
    }}
  }} catch(e) {{}}
  window.close();
}}

function doSearch() {{
  var term = (document.querySelector('[name=x_thefilter]').value || '').toLowerCase();
  var filtered = term
    ? ALL_OPTIONS.filter(function(o) {{ return o.toLowerCase().includes(term); }})
    : ALL_OPTIONS;
  var div = document.getElementById('results');
  div.innerHTML = filtered.map(function(o) {{
    return '<a href="#" onclick="event.preventDefault(); pick(' + JSON.stringify(o) + ');">' + o + '</a><br>';
  }}).join('');
}}

document.querySelector('button').addEventListener('click', doSearch);
doSearch();
</script>
</body>
</html>"""


def _programme_popup_html() -> str:
    """Programme LOV popup — two-column table (code + description).

    adapter's select_programme_from_lov:
      - reads all tr innerText via evaluate()
      - best_programme_match picks the eligible one
      - clicks tr.querySelector('a') of the matching row
    """
    rows_html = ""
    for code, desc in _PROGRAMME_ROWS:
        rows_html += (
            f'<tr>'
            f'<td><a href="#" onclick="event.preventDefault(); pick({json.dumps(code)});">'
            f'{code}</a></td>'
            f'<td>{desc}</td>'
            f'</tr>\n'
        )

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Select Programme</title></head>
<body>
<div>
  <input type="text" name="x_thefilter" placeholder="Filter...">
  <button type="button">Search</button>
</div>
<div id="results">
<table id="prog-table">
{rows_html}
</table>
</div>
<script>
function pick(code) {{
  try {{
    var opener = window.opener;
    if (opener) {{
      var el = opener.document.querySelector('#oapQualification');
      if (el) {{
        el.value = code;
        el.dispatchEvent(new Event('change', {{bubbles: true}}));
      }}
    }}
  }} catch(e) {{}}
  window.close();
}}

document.querySelector('button').addEventListener('click', function() {{
  var term = (document.querySelector('[name=x_thefilter]').value || '').toUpperCase().trim();
  var rows = document.querySelectorAll('#prog-table tr');
  rows.forEach(function(tr) {{
    var show = !term || term === '%' || (tr.innerText || '').toUpperCase().includes(term);
    tr.style.display = show ? '' : 'none';
  }});
}});
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Page handlers
# ---------------------------------------------------------------------------

async def handle_popi_gate(request: web.Request) -> web.Response:
    body = """
<form action="/popi" method="post">
  <p>
    <label>Do you have a student number?</label>
    <select id="oapOldNew" name="oapOldNew">
      <option value="">--</option><option value="Y">Yes</option><option value="N">No</option>
    </select>
  </p>
  <p>
    <label>Returning applicant?</label>
    <select id="oapReturnYesNo" name="oapReturnYesNo">
      <option value="">--</option><option value="Y">Yes</option><option value="N">No</option>
    </select>
  </p>
  <p>
    <label>Do you have a token?</label>
    <select id="oapTokenYesNo" name="oapTokenYesNo">
      <option value="">--</option><option value="Y">Yes</option><option value="N">No</option>
    </select>
  </p>
  <p>
    <input type="checkbox" id="oapAcceptPopi" name="oapAcceptPopi">
    <label for="oapAcceptPopi">I accept the POPI/PAIA terms and conditions</label>
  </p>
  <p><input type="submit" id="oapNextBtn1" value="Next"></p>
</form>"""
    return _page("UJ Online Application — Entry", body)


async def handle_page_a(request: web.Request) -> web.Response:
    body = """
<form action="/page-a" method="post">
  <p><label>SA Citizen
    <select id="oapCitizenType" name="oapCitizenType">
      <option value="">--</option><option>Yes</option><option>No</option>
    </select></label></p>
  <p><label>ID Number <input type="text" id="oapIDnumber" name="oapIDnumber"></label></p>
  <p><label>Citizenship Code """ + _lov_trigger("oapCitzCode", "Citizenship") + """</label></p>
  <p style="display:none"><label>Gender
    <select id="oapGender" name="oapGender" style="display:none">
      <option value="">--</option>
      <option>F Female</option><option>M Male</option>
    </select></label></p>
  <p><label>Date of Birth (DD-MON-YYYY)
    <input type="text" id="oapBirthdate" name="oapBirthdate" readonly></label></p>
  <p><label>Title
    <select id="oapTitle" name="oapTitle">
      <option value="">--</option>
      <option>ADV</option><option>DR</option><option>MISS</option>
      <option>MR</option><option>MRS</option><option>PAST</option><option>PROF</option>
    </select></label></p>
  <p><label>Initials <input type="text" id="oapInitials" name="oapInitials"></label></p>
  <p><label>Surname <input type="text" id="oapSurname" name="oapSurname"></label></p>
  <p><label>First names <input type="text" id="oapFirstNames" name="oapFirstNames"></label></p>
  <p><label>Maiden name <input type="text" id="oapMaiden" name="oapMaiden"></label></p>
  <p><label>Marital status
    <select id="oapMaritalStatus" name="oapMaritalStatus">
      <option value="">--</option>
      <option>Single</option><option>Married</option>
      <option>Divorced</option><option>Widow/er</option>
    </select></label></p>
  <p><label>Home language
    <select id="oapHomeLang" name="oapHomeLang">
      <option value="">--</option>
      <option>AFRIKAANS</option><option>AFRIKAANS/ENGLISH</option>
      <option>ANOTHER LANGUAGE</option><option>ENGLISH</option>
      <option>EUROPEAN LANGUAGE</option>
    </select></label></p>
  <p><label>Ethnic group
    <select id="oapEthnic" name="oapEthnic">
      <option value="">--</option>
      <option>AFRICAN</option><option>COLOURED</option>
      <option>INDIAN</option><option>OTHER</option><option>WHITE</option>
    </select></label></p>
  <p><label>Source of funding
    <select id="oapSourcefund" name="oapSourcefund">
      <option value="">--</option>
      <option>NSFAS</option><option>Self Paying</option><option>Other</option>
    </select></label></p>
  <p><label>Street Address 1 <input type="text" id="oapStreetAddr1" name="oapStreetAddr1"></label></p>
  <p><label>Street Address 2 <input type="text" id="oapStreetAddr2" name="oapStreetAddr2"></label></p>
  <p><label>Street Address 3 <input type="text" id="oapStreetAddr3" name="oapStreetAddr3"></label></p>
  <p><label>Street Address 4 <input type="text" id="oapStreetAddr4" name="oapStreetAddr4"></label></p>
  <p><label>Postal Code """ + _lov_trigger("oapStreetAddrPCodeRq", "Code") + """</label></p>
  <p><label>SA Cell?
    <select id="oapCellInd" name="oapCellInd">
      <option value="">--</option><option>Yes</option><option>No</option>
    </select></label></p>
  <p><label>SA Cell <input type="text" id="oapSACell" name="oapSACell"></label></p>
  <p><label>Email <input type="text" id="itsEmail" name="itsEmail"></label></p>
  <p><label>Verify email <input type="text" id="verifyEmail" name="verifyEmail"></label></p>
  <p><label>Apply for residence?
    <select id="oapResReq" name="oapResReq">
      <option value="">--</option><option>Yes</option><option>No</option>
    </select></label></p>
  <p><label>
    <input type="checkbox" id="oapApplyDisability" name="oapApplyDisability">
    Disability or impairment?</label></p>
  <p><input type="submit" id="oapNextBtn2" value="Save and Continue"></p>
</form>"""
    return _page("UJ — Page A: Biographical", body)


async def handle_page_b(request: web.Request) -> web.Response:
    body = """
<form action="/page-b" method="post">
  <h2>Next of Kin</h2>
  <p><label>NOK Name <input type="text" id="oapNokName" name="oapNokName"></label></p>
  <p><label>NOK Mobile <input type="text" id="oapNokMobileNr" name="oapNokMobileNr"></label></p>
  <h2>Account Contact</h2>
  <p><label>Name <input type="text" id="oapAcntName" name="oapAcntName"></label></p>
  <p><label>Mobile <input type="text" id="oapAcntMobileNr" name="oapAcntMobileNr"></label></p>
  <p><label>Addr 1 <input type="text" id="oapAcntPostalAddr1" name="oapAcntPostalAddr1"></label></p>
  <p><label>Addr 2 <input type="text" id="oapAcntPostalAddr2" name="oapAcntPostalAddr2"></label></p>
  <p><label>Addr 3 <input type="text" id="oapAcntPostalAddr3" name="oapAcntPostalAddr3"></label></p>
  <p><label>Addr 4 <input type="text" id="oapAcntPostalAddr4" name="oapAcntPostalAddr4"></label></p>
  <p><label>Postal Code """ + _lov_trigger("oapAcntPostalCode", "Code") + """</label></p>
  <p><label>Email <input type="text" id="oapAcntEmail" name="oapAcntEmail"></label></p>
  <p><input type="submit" id="oapNextBtn2_1" value="Save and Continue"></p>
</form>"""
    return _page("UJ — Page B: Next of Kin & Account Contact", body)


async def handle_page_c(request: web.Request) -> web.Response:
    body = """
<form action="/page-c" method="post">
  <p><label>Matric Year <input type="text" id="oapMatYear" name="oapMatYear"></label></p>
  <p><label>UG/PG
    <select id="oapUGPGUGOnly" name="oapUGPGUGOnly">
      <option value="">--</option><option>Undergraduate</option>
    </select></label></p>
  <p><label>Upgrading?
    <select id="oapStudUpgrade" name="oapStudUpgrade">
      <option value="">--</option><option>Yes</option><option>No</option>
    </select></label></p>
  <p><label>Matric type
    <select id="oapTypeMatric" name="oapTypeMatric">
      <option value="">--</option>
      <option>SA Matric</option><option>International Matric</option>
    </select></label></p>
  <p><label>Endorsement """ + _lov_trigger("oapMatType", "Endorsement") + """</label></p>
  <p><label>Exam number <input type="text" id="oapExamNum" name="oapExamNum"></label></p>
  <hr>
  <h3>Add Subject</h3>
  <p><label>Subject """ + _lov_trigger("oapMSubj", "Subject") + """</label></p>
  <p><label>Grade """ + _lov_trigger("oapMGrade", "Grade") + """</label></p>
  <p><label>Gr11 % """ + _lov_trigger("oapsymbGr11", "Percentage") + """</label></p>
  <p><button type="button" id="oapAddMatric"
      onclick="this.insertAdjacentHTML('afterend',
        '<p>✓ Subject row added</p>')">Add Subject</button></p>
  <p><input type="submit" id="oapNextBtn3" value="Save and Continue"></p>
</form>"""
    return _page("UJ — Page C: Matric Results", body)


async def handle_page_d(request: web.Request) -> web.Response:
    body = """
<form action="/page-d" method="post">
  <p><label>School """ + _lov_trigger("oapSchool", "School") + """</label></p>
  <p><label>Present activity """ + _lov_trigger("oapPact", "Activity") + """</label></p>
  <p><label>Studied before?
    <select id="oapPrevQualInd" name="oapPrevQualInd">
      <option value="">--</option><option>Yes</option><option>No</option>
    </select></label></p>
  <p><input type="submit" id="oapNextBtn4" value="Save and Continue"></p>
</form>"""
    return _page("UJ — Page D: Previous Studies", body)


async def handle_page_e(request: web.Request) -> web.Response:
    body = """
<form action="/page-e" method="post">
  <p><label>Academic Year
    <select id="oapAcademicYear" name="oapAcademicYear">
      <option value="">--</option><option>2027</option><option>2026</option>
    </select></label></p>
  <p><label>Applying for
    <select id="oapECSLP" name="oapECSLP">
      <option value="">--</option>
      <option>Curricular Courses</option>
      <option>Continuing Education Programmes (CEP)</option>
      <option>Short Learning Programs (SLP)</option>
    </select></label></p>
  <p><label>Faculty """ + _lov_trigger("oapFaculty", "Faculty") + """</label></p>
  <p><label>Programme """ + _lov_trigger("oapQualification", "Programme") + """</label></p>
  <p><label>Year of study """ + _lov_trigger("oapStudyPeriod", "Year") + """</label></p>
  <p><label>Mode of study """ + _lov_trigger("oapOfferingType", "Mode") + """</label></p>
  <p><input type="submit" id="oapNextBtn6" value="Save and Continue" disabled></p>
</form>"""
    return _page("UJ — Page E: Qualifications", body)


async def handle_page_f(request: web.Request) -> web.Response:
    body = """
<p>Please review your application summary.</p>
<form action="/page-f" method="post">
  <button type="submit">Continue</button>
</form>"""
    return _page("UJ — Page F: Summary", body)


async def handle_page_g(request: web.Request) -> web.Response:
    body = """
<div style="background:#fffde7;border:2px solid #f9a825;padding:16px;margin:16px 0;">
  <strong>Test mode — Submit is blocked.</strong>
  The adapter reached Page G (Rules &amp; Agreement) successfully.
  No application was submitted.
</div>
<p>In production, the student would enter their PIN and submit here.</p>"""
    return _page("UJ — Page G: Rules & Agreement (TEST MODE)", body)


async def handle_lov(request: web.Request) -> web.Response:
    field_id = request.match_info["field"]
    if field_id == "oapQualification":
        return web.Response(text=_programme_popup_html(), content_type="text/html")
    options = _LOV.get(field_id, [f"Option A for {field_id}", f"Option B for {field_id}"])
    return web.Response(text=_lov_popup_html(field_id, options), content_type="text/html")


def _redirect(target: str):
    async def handler(request: web.Request) -> web.Response:
        raise web.HTTPFound(target)
    return handler


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

def make_uj_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_popi_gate)
    app.router.add_post("/popi", _redirect("/page-a"))
    app.router.add_get("/page-a", handle_page_a)
    app.router.add_post("/page-a", _redirect("/page-b"))
    app.router.add_get("/page-b", handle_page_b)
    app.router.add_post("/page-b", _redirect("/page-c"))
    app.router.add_get("/page-c", handle_page_c)
    app.router.add_post("/page-c", _redirect("/page-d"))
    app.router.add_get("/page-d", handle_page_d)
    app.router.add_post("/page-d", _redirect("/page-e"))
    app.router.add_get("/page-e", handle_page_e)
    app.router.add_post("/page-e", _redirect("/page-f"))
    app.router.add_get("/page-f", handle_page_f)
    app.router.add_post("/page-f", _redirect("/page-g"))
    app.router.add_get("/page-g", handle_page_g)
    app.router.add_get("/lov/{field}", handle_lov)
    return app
