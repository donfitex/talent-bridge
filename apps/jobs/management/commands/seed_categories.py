from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.jobs.models import JobCategory, Skill

CATEGORIES = [
    (
        "Software Engineering",
        "bi-code-slash",
        "Software development, architecture, testing, and engineering roles.",
    ),
    (
        "Data Science",
        "bi-bar-chart",
        "Data analysis, machine learning, AI, and big data engineering.",
    ),
    (
        "Cybersecurity",
        "bi-shield-lock",
        "Information security, compliance, network defense, and cryptography.",
    ),
    (
        "Product Management",
        "bi-kanban",
        "Product strategy, roadmap execution, and technical product leadership.",
    ),
    ("Design", "bi-palette", "UI/UX design, graphic design, user research, and branding."),
    (
        "Marketing",
        "bi-megaphone",
        "Growth marketing, SEO, content creation, and digital brand management.",
    ),
    ("Finance", "bi-cash-coin", "Financial planning, accounting, investment, and risk analysis."),
    (
        "Human Resources",
        "bi-people",
        "Talent acquisition, employee relations, and people operations.",
    ),
    (
        "Healthcare",
        "bi-heart-pulse",
        "Clinical care, biomedical engineering, and health informatics.",
    ),
    ("Engineering", "bi-gear", "Mechanical, electrical, civil, and industrial engineering."),
    (
        "Education",
        "bi-mortarboard",
        "Teaching, training, curriculum design, and educational technology.",
    ),
    (
        "Sales",
        "bi-graph-up-arrow",
        "Business development, enterprise account sales, and client acquisition.",
    ),
    (
        "Customer Support",
        "bi-headset",
        "Customer success, support engineering, and client services.",
    ),
    ("Logistics", "bi-truck", "Supply chain coordination, warehousing, and inventory management."),
    (
        "Operations",
        "bi-sliders",
        "Business operations, continuous improvement, and organizational efficiency.",
    ),
    (
        "Manufacturing",
        "bi-tools",
        "Production scheduling, plant management, and quality assurance.",
    ),
    (
        "Administration",
        "bi-clipboard-check",
        "Office management, executive administration, and clerical workflows.",
    ),
]

COMMON_SKILLS = {
    "Software Engineering": [
        "Python",
        "Django",
        "JavaScript",
        "TypeScript",
        "React",
        "PostgreSQL",
        "Docker",
        "Git",
        "REST APIs",
        "AWS",
    ],
    "Data Science": [
        "Pandas",
        "NumPy",
        "TensorFlow",
        "PyTorch",
        "SQL",
        "Scikit-Learn",
        "Data Visualization",
    ],
    "Product Management": [
        "Agile",
        "Scrum",
        "Product Roadmapping",
        "User Stories",
        "Market Research",
        "Jira",
    ],
    "Design": ["Figma", "Adobe XD", "UI Design", "UX Research", "Prototyping", "Wireframing"],
}


class Command(BaseCommand):
    help = "Seeds initial job categories and standard skills"

    def handle(self, *args, **options):
        from apps.jobs.catalog import SEARCHES

        categories = list(CATEGORIES)
        known = {item[0] for item in categories}
        categories.extend(
            (name, "bi-briefcase", f"{name} opportunities in Nigeria.")
            for name in SEARCHES
            if name not in known
        )
        count = 0
        for name, icon, desc in categories:
            cat, created = JobCategory.objects.get_or_create(
                name=name,
                defaults={
                    "slug": slugify(name),
                    "icon": icon,
                    "description": desc,
                    "is_active": True,
                },
            )
            if created:
                count += 1

            if name in COMMON_SKILLS:
                for skill_name in COMMON_SKILLS[name]:
                    Skill.objects.get_or_create(
                        slug=slugify(skill_name),
                        defaults={"name": skill_name, "category": cat, "is_verified": True},
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {count} job categories and initial skills taxonomy."
            )
        )
