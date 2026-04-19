# ── Expanded skill database (150+ skills, lowercase) ──
SKILLS_DB = [
    # Languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "golang",
    "rust", "swift", "kotlin", "scala", "ruby", "php", "r", "matlab", "perl",
    "bash", "shell", "powershell", "dart", "lua", "haskell", "elixir",

    # Web Frontend
    "html", "css", "react", "reactjs", "react.js", "vue", "vuejs", "vue.js",
    "angular", "angularjs", "svelte", "nextjs", "next.js", "nuxtjs", "jquery",
    "bootstrap", "tailwind", "tailwindcss", "sass", "less", "webpack", "vite",
    "redux", "zustand", "graphql",

    # Web Backend
    "nodejs", "node.js", "express", "expressjs", "django", "flask", "fastapi",
    "spring", "springboot", "spring boot", "laravel", "rails", "ruby on rails",
    "asp.net", "dotnet", ".net", "nestjs", "hapi",

    # Databases
    "sql", "mysql", "postgresql", "postgres", "sqlite", "mongodb", "redis",
    "elasticsearch", "cassandra", "dynamodb", "firebase", "supabase",
    "oracle", "mssql", "neo4j", "influxdb", "cockroachdb",

    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "ci/cd", "github actions", "gitlab ci",
    "nginx", "apache", "linux", "unix", "heroku", "vercel", "netlify",

    # Data Science / ML / AI
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "data science", "data analysis", "data engineering",
    "pandas", "numpy", "scipy", "matplotlib", "seaborn", "plotly",
    "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
    "hugging face", "transformers", "langchain", "openai", "llm",
    "xgboost", "lightgbm", "spark", "pyspark", "hadoop", "hive",
    "tableau", "power bi", "looker", "dbt", "airflow", "mlflow",

    # Mobile
    "android", "ios", "react native", "flutter", "xamarin", "ionic",

    # Tools & Other
    "git", "github", "gitlab", "bitbucket", "jira", "confluence", "notion",
    "figma", "postman", "swagger", "graphql", "rest", "restful", "grpc",
    "microservices", "system design", "object oriented", "oop",
    "agile", "scrum", "kanban", "tdd", "unit testing", "pytest",
    "selenium", "cypress", "jest", "mocha",

    # Security
    "cybersecurity", "penetration testing", "ethical hacking", "linux security",
    "owasp", "cryptography", "network security",

    # Blockchain
    "blockchain", "solidity", "web3", "ethereum", "smart contracts",
]


def extract_skills(text: str) -> list:
    """Extract skills from resume text using keyword matching."""
    found = set()
    text_lower = text.lower()

    for skill in SKILLS_DB:
        # Word-boundary safe check — avoid matching 'r' inside 'array'
        skill_lower = skill.lower()
        idx = text_lower.find(skill_lower)
        while idx != -1:
            before = text_lower[idx - 1] if idx > 0 else ' '
            after  = text_lower[idx + len(skill_lower)] if idx + len(skill_lower) < len(text_lower) else ' '
            # Only match if surrounded by non-alphanumeric (word boundary)
            if not before.isalnum() and not after.isalnum():
                found.add(skill.title())
                break
            idx = text_lower.find(skill_lower, idx + 1)

    return list(found)