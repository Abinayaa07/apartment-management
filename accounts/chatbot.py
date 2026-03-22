import re


FAQ_ENTRIES = [
    {
        "keywords": ["register", "registration", "sign up", "signup", "create account"],
        "answer": (
            "To register, open the Register page and fill in your basic details. "
            "Residents should also upload ID proof and address proof. After registration, "
            "resident accounts stay pending until admin approval."
        ),
    },
    {
        "keywords": ["approval", "approved", "pending approval", "why can't i login", "cannot login"],
        "answer": (
            "If you are a resident, your account must be approved by admin before login works. "
            "Once approved, you can sign in normally from the Login page."
        ),
    },
    {
        "keywords": ["login", "sign in", "password", "forgot password"],
        "answer": (
            "Use your username and password on the Login page. If login fails, first check whether "
            "your resident account is approved. For admin access, use the /admin/ page with your admin credentials."
        ),
    },
    {
        "keywords": ["ticket", "complaint", "maintenance", "issue", "raise ticket"],
        "answer": (
            "Residents can create a maintenance ticket from the dashboard or Tickets section. "
            "Add a title, description, category, and optional image. Staff and admin can review and update ticket status."
        ),
    },
    {
        "keywords": ["payment", "dues", "maintenance dues", "upi", "cash", "pay"],
        "answer": (
            "Maintenance dues appear in the Payments section. Residents can pay pending dues using "
            "UPI or Cash, and paid records appear in Payment History. Staff and admin can assign new dues from their dashboard."
        ),
    },
    {
        "keywords": ["visitor", "guest", "entry", "exit", "vehicle", "security gate"],
        "answer": (
            "Security can add visitor entry logs with name, phone, purpose, flat number, and vehicle number. "
            "When the visitor leaves, security can mark the exit from the visitor log page."
        ),
    },
    {
        "keywords": ["notice", "announcement", "board", "staff notice", "security notice"],
        "answer": (
            "Notices are published from the Notice section. A notice can target All, Staff, or Security. "
            "Users only see the notices that match their role."
        ),
    },
    {
        "keywords": ["role", "admin", "staff", "security", "resident"],
        "answer": (
            "The system has four roles: Resident, Security, Staff, and Admin. Residents use tickets, dues, and notices. "
            "Security manages visitors. Staff handles notices, tickets, and payments. Admin oversees approvals and overall management."
        ),
    },
    {
        "keywords": ["document", "id proof", "address proof", "verification"],
        "answer": (
            "Resident registration includes document verification. ID proof and address proof are required, "
            "and admin reviews them before approving the account."
        ),
    },
    {
        "keywords": ["dashboard", "what can i do", "features", "how to use"],
        "answer": (
            "The dashboard changes by role. Residents can raise tickets and pay dues. Security handles visitor logs. "
            "Staff manages notices, tickets, and payments. Admin can review users, approvals, analytics, and society operations."
        ),
    },
]

DEFAULT_REPLY = (
    "I can help with registration, approvals, login, tickets, dues, notices, visitor entry, roles, and document verification. "
    "Try asking something like 'How do I pay maintenance dues?' or 'Why is my account pending approval?'."
)

SUGGESTED_QUESTIONS = [
    "How do I register as a resident?",
    "Why is my login pending approval?",
    "How do I raise a maintenance ticket?",
    "How do I pay maintenance dues?",
]


def _normalize(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def get_faq_answer(message):
    question = _normalize(message)
    if not question:
        return {
            "answer": DEFAULT_REPLY,
            "matched": False,
            "suggestions": SUGGESTED_QUESTIONS,
        }

    best_answer = None
    best_score = 0

    for entry in FAQ_ENTRIES:
        score = 0
        for keyword in entry["keywords"]:
            keyword_norm = _normalize(keyword)
            if keyword_norm in question:
                score += max(1, len(keyword_norm.split()))
        if score > best_score:
            best_score = score
            best_answer = entry["answer"]

    if best_answer:
        return {
            "answer": best_answer,
            "matched": True,
            "suggestions": SUGGESTED_QUESTIONS,
        }

    return {
        "answer": DEFAULT_REPLY,
        "matched": False,
        "suggestions": SUGGESTED_QUESTIONS,
    }
