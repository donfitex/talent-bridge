"""Nigeria sector searches. One representative query per category per cycle."""

SEARCHES = {
    "Software Engineering": "software engineer",
    "Data Science": "data analyst",
    "Cybersecurity": "cybersecurity",
    "Product Management": "product manager",
    "Design": "graphic designer",
    "Marketing": "marketing",
    "Finance": "accountant",
    "Human Resources": "human resources",
    "Healthcare": "nurse medical",
    "Engineering": "engineer",
    "Education": "teacher",
    "Sales": "sales",
    "Customer Support": "customer service",
    "Logistics": "logistics",
    "Operations": "operations",
    "Manufacturing": "production manufacturing",
    "Administration": "administrative officer",
    "Agriculture": "agriculture farm",
    "Banking and Insurance": "banking insurance",
    "Construction": "construction",
    "Legal": "legal lawyer",
    "Hospitality and Tourism": "hotel hospitality",
    "Food Services": "chef cook",
    "Retail": "retail store",
    "Oil and Gas": "oil gas petroleum",
    "Energy and Utilities": "energy solar",
    "Telecommunications": "telecommunications",
    "Information Technology": "IT support",
    "Media and Communications": "communications journalist",
    "NGO and Development": "NGO development",
    "Public Sector": "government public sector",
    "Research": "research scientist",
    "Real Estate": "real estate",
    "Procurement": "procurement purchasing",
    "Security": "security officer",
    "Transport and Driving": "driver transport",
    "Skilled Trades": "electrician technician",
    "Cleaning and Facilities": "cleaner facilities",
    "Health and Safety": "health safety HSE",
    "Quality Assurance": "quality assurance",
    "Project Management": "project manager",
    "Business Management": "business manager",
    "Internships and Graduate Roles": "graduate trainee internship",
    "Social Services": "social worker",
    "Arts and Entertainment": "creative arts",
    "Other Jobs": "general worker",
}


def classify(title):
    import re

    words = set(re.findall(r"[a-z]+", title.lower()))
    scores = [
        (len(words & set(query.split())), category)
        for category, query in SEARCHES.items()
        if category != "Other Jobs"
    ]
    score, category = max(scores, key=lambda item: item[0])
    return category if score else "Other Jobs"
