"""
Seed questions v2 — role-specific, mixed types, conditional sub-questions.
Run: venv\Scripts\python.exe scripts/seed_questions_v2.py
"""
import sys, uuid, json
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.core import models
from sqlalchemy import text, func

db = SessionLocal()

# ── helpers ───────────────────────────────────────────────────────────────────

def cat_id(name: str):
    row = db.query(models.Category).filter(models.Category.name == name).first()
    if not row:
        print(f"  [WARN] Category not found: {name}")
    return row.id if row else None

def make_q(label, cat_name, order, atype="text", options=None, required=True):
    cid = cat_id(cat_name)
    if not cid:
        return None
    q = models.Question(
        id=uuid.uuid4(), label=label, answer_type=atype,
        options=json.dumps(options) if options else None,
        is_required=required, display_order=order,
        status="active", category_id=cid
    )
    db.add(q)
    db.flush()
    return q

def make_sub(label, parent_q, trigger_value, order, atype="text", options=None, required=False):
    """Sub-question triggered when parent answer contains trigger_value."""
    if parent_q is None:
        return None
    q = models.Question(
        id=uuid.uuid4(), label=label, answer_type=atype,
        options=json.dumps(options) if options else None,
        is_required=required, display_order=order,
        status="active", category_id=parent_q.category_id,
        parent_question_id=parent_q.id
    )
    db.add(q)
    db.flush()

    # Find the option that matches trigger_value
    opt = None
    if parent_q.question_options:
        opt = next((o for o in parent_q.question_options if trigger_value.lower() in o.option_text.lower()), None)

    cond = models.QuestionCondition(
        id=uuid.uuid4(),
        question_id=q.id,
        trigger_question_id=parent_q.id,
        trigger_option_id=opt.id if opt else None,
        trigger_value=trigger_value,
        trigger_value_operator="contains",
        logical_operator="OR",
        priority=1,
        is_required=required
    )
    db.add(cond)
    db.flush()
    return q

def make_opts(q_obj, option_texts):
    """Attach QuestionOption rows to a question and return the list."""
    opts = []
    for i, txt in enumerate(option_texts):
        o = models.QuestionOption(id=uuid.uuid4(), question_id=q_obj.id,
                                  option_text=txt, display_order=i + 1)
        db.add(o)
        opts.append(o)
    db.flush()
    return opts

# ── wipe existing questions ───────────────────────────────────────────────────
try:
    db.execute(text("DELETE FROM question_conditions"))
    db.execute(text("DELETE FROM question_options"))
    db.execute(text("DELETE FROM questions"))
    db.commit()
    print("Cleared existing questions.")
except Exception as e:
    db.rollback()
    print("Error clearing:", e)
    sys.exit(1)

# ─────────────────────────── GENERAL ─────────────────────────────────────────
gen = db.query(models.Category).filter(models.Category.is_general == True).first()
if not gen:
    gen = models.Category(id=uuid.uuid4(), name="Informations Generales",
                          is_general=True, status="active")
    db.add(gen)
    db.flush()

def gq(label, order, atype="text", options=None):
    q = models.Question(id=uuid.uuid4(), label=label, answer_type=atype,
        options=json.dumps(options) if options else None,
        is_required=True, display_order=order, status="active", category_id=gen.id)
    db.add(q)
    db.flush()
    if options:
        make_opts(q, options)
    return q

gq("Nom complet du projet", 1)
gq("Decrivez en quelques phrases l objectif principal du projet", 2)
gq("Qui sont les utilisateurs finaux de ce projet ?", 3)
q_budget = gq("Quel est votre budget estimé ?", 4, "single_choice",
    ["Moins de 500 DT", "500 – 2 000 DT", "2 000 – 10 000 DT", "Plus de 10 000 DT", "Pas encore défini"])
make_sub("Précisez votre budget approximatif (montant + devise)", q_budget, "Pas encore défini", 1, "text")

gq("Quelle est la date limite souhaitée pour la livraison ?", 5)
gq("Dans quelle langue doit être livré le résultat final ?", 6, "single_choice",
    ["Français", "Arabe", "Anglais", "Bilingue FR/EN", "Autre"])

print("General questions seeded.")

# ─────────────────── INFORMATION TECHNOLOGY ──────────────────────────────────

# ── Full-Stack Developer ──────────────────────────────────────────────────────
q1 = make_q("Quel type d application souhaitez-vous développer ?", "Full-Stack Developer", 1,
    "single_choice", ["Application web", "Application mobile", "API / Backend uniquement", "Dashboard / Back-office"])
if q1:
    make_opts(q1, q1.options and json.loads(q1.options) or [])
    make_sub("Quel sera le nom de domaine / URL de l application ?", q1, "Application web", 1)
    make_sub("Sur quelle plateforme mobile ?", q1, "Application mobile", 1,
        "single_choice", ["iOS", "Android", "Les deux (React Native / Flutter)"])

q2 = make_q("Votre application nécessite-t-elle une authentification ?", "Full-Stack Developer", 2,
    "single_choice", ["Oui — Email / Mot de passe", "Oui — OAuth (Google, Facebook)", "Oui — SSO entreprise", "Non"])
if q2:
    make_opts(q2, json.loads(q2.options))
    make_sub("La gestion des rôles est-elle requise ? (admin, éditeur, visiteur…)", q2, "Oui", 1,
        "single_choice", ["Oui, plusieurs rôles", "Non, un seul rôle"])

make_q("Quelle base de données préférez-vous ?", "Full-Stack Developer", 3,
    "single_choice", ["PostgreSQL", "MySQL", "MongoDB", "Firebase", "Pas de préférence"])
make_q("Le projet nécessite-t-il des notifications (email, SMS, push) ?", "Full-Stack Developer", 4,
    "multi_choice", ["Notifications email", "SMS", "Push (mobile/web)", "Aucune"])
make_q("Hébergement souhaité ?", "Full-Stack Developer", 5,
    "single_choice", ["AWS", "Azure", "GCP", "VPS (OVH, Hetzner…)", "Pas de préférence"])
make_q("Combien d utilisateurs simultanés attendez-vous au lancement ?", "Full-Stack Developer", 6,
    "single_choice", ["Moins de 100", "100 à 1 000", "1 000 à 10 000", "Plus de 10 000"])

# ── Front-End Developer ───────────────────────────────────────────────────────
q1 = make_q("Avez-vous déjà des maquettes ou un design ?", "Front-End Developer", 1,
    "single_choice", ["Oui — Figma fourni", "Oui — Adobe XD fourni", "Non — à créer", "Partiellement"])
if q1:
    make_opts(q1, json.loads(q1.options))
    make_sub("Quel outil de design a été utilisé ?", q1, "Non", 1, "text")

make_q("Quel framework frontend souhaitez-vous ?", "Front-End Developer", 2,
    "single_choice", ["React", "Vue.js", "Angular", "Next.js", "Pas de préférence"])
make_q("Le site doit-il être responsive (mobile + desktop) ?", "Front-End Developer", 3,
    "single_choice", ["Oui — les deux", "Desktop uniquement", "Mobile uniquement"])
make_q("Des animations ou transitions spéciales sont-elles requises ?", "Front-End Developer", 4,
    "single_choice", ["Oui — animations avancées", "Oui — transitions légères", "Non"])
make_q("Le SEO est-il important pour ce projet ?", "Front-End Developer", 5,
    "single_choice", ["Oui — très important", "Oui — basique", "Non"])

# ── Back-End Developer ────────────────────────────────────────────────────────
make_q("Quel type d API faut-il développer ?", "Back-End Developer", 1,
    "single_choice", ["REST", "GraphQL", "gRPC", "WebSocket (temps réel)", "Les deux (REST + WS)"])
make_q("Quelle architecture préférez-vous ?", "Back-End Developer", 2,
    "single_choice", ["Monolithique", "Microservices", "Serverless", "Pas de préférence"])
q3 = make_q("Le système nécessite-t-il un traitement en temps réel ?", "Back-End Developer", 3,
    "single_choice", ["Oui", "Non"])
if q3:
    make_opts(q3, json.loads(q3.options))
    make_sub("Quel volume de messages / événements par seconde ?", q3, "Oui", 1, "text")
make_q("Quel langage backend préférez-vous ?", "Back-End Developer", 4,
    "single_choice", ["Python (FastAPI / Django)", "Node.js (Express)", "Java (Spring Boot)", "PHP (Laravel)", "Pas de préférence"])
make_q("Une documentation API est-elle requise (Swagger / OpenAPI) ?", "Back-End Developer", 5,
    "single_choice", ["Oui", "Non"])

# ── Mobile App Developer ──────────────────────────────────────────────────────
make_q("Plateforme cible de l application", "Mobile App Developer (iOS/Android)", 1,
    "single_choice", ["iOS uniquement", "Android uniquement", "iOS + Android natif", "Cross-platform (Flutter)", "Cross-platform (React Native)"])
make_q("L application fonctionnera-t-elle hors ligne ?", "Mobile App Developer (iOS/Android)", 2,
    "single_choice", ["Oui — mode hors-ligne complet", "Oui — partiellement", "Non"])
q3 = make_q("Quelles fonctionnalités natives sont nécessaires ?", "Mobile App Developer (iOS/Android)", 3,
    "multi_choice", ["GPS / Géolocalisation", "Caméra / Scanner QR", "Paiement in-app", "Notifications push", "Biométrie (Face ID / Touch ID)", "Bluetooth / NFC", "Aucune"])
make_q("L application doit-elle être publiée sur les stores ?", "Mobile App Developer (iOS/Android)", 4,
    "single_choice", ["Oui — App Store et Google Play", "Oui — Google Play uniquement", "Oui — App Store uniquement", "Non — distribution interne"])
make_q("Un back-office / tableau de bord admin est-il requis ?", "Mobile App Developer (iOS/Android)", 5,
    "single_choice", ["Oui", "Non"])

# ── DevOps Engineer ───────────────────────────────────────────────────────────
make_q("Quel cloud provider utilisez-vous ou préférez-vous ?", "DevOps Engineer", 1,
    "single_choice", ["AWS", "Azure", "GCP", "OVH / VPS", "On-premise", "Multi-cloud"])
make_q("Un pipeline CI/CD est-il requis ?", "DevOps Engineer", 2,
    "single_choice", ["Oui — GitHub Actions", "Oui — GitLab CI/CD", "Oui — Jenkins", "Non"])
make_q("La conteneurisation est-elle nécessaire ?", "DevOps Engineer", 3,
    "single_choice", ["Docker uniquement", "Kubernetes (orchestration)", "Docker + Kubernetes", "Non"])
make_q("Quel niveau de haute disponibilité est requis ?", "DevOps Engineer", 4,
    "single_choice", ["99.9% (standard)", "99.99% (haute dispo)", "Pas de contrainte"])
make_q("Des outils de monitoring sont-ils requis ?", "DevOps Engineer", 5,
    "multi_choice", ["Grafana / Prometheus", "Datadog", "ELK Stack (logs)", "PagerDuty (alertes)", "Non requis"])

# ── Cloud Engineer ────────────────────────────────────────────────────────────
make_q("Quel est le contexte de la mission cloud ?", "Cloud Engineer", 1,
    "single_choice", ["Migration vers le cloud", "Nouvelle infrastructure cloud", "Optimisation des coûts", "Sécurité et conformité"])
make_q("Quels services cloud sont concernés ?", "Cloud Engineer", 2,
    "multi_choice", ["Stockage (S3, Blob)", "Bases de données managées", "Serverless (Lambda, Functions)", "CDN / Edge", "IAM / Sécurité"])
make_q("La solution doit-elle être multi-région ?", "Cloud Engineer", 3,
    "single_choice", ["Oui", "Non"])
make_q("La FinOps (optimisation des coûts cloud) est-elle un objectif ?", "Cloud Engineer", 4,
    "single_choice", ["Oui — priorité importante", "Oui — secondaire", "Non"])

# ── Software Engineer ─────────────────────────────────────────────────────────
make_q("Quel type de logiciel faut-il développer ?", "Software Engineer", 1,
    "single_choice", ["Application desktop", "Application web", "Outil CLI / script", "Bibliothèque / SDK", "Système embarqué"])
make_q("Quel langage de programmation préférez-vous ?", "Software Engineer", 2,
    "single_choice", ["Python", "Java", "C# (.NET)", "C++", "Go", "Pas de préférence"])
make_q("Des tests automatisés sont-ils requis ?", "Software Engineer", 3,
    "single_choice", ["Oui — tests unitaires", "Oui — tests d intégration", "Oui — les deux", "Non"])
make_q("Une documentation technique est-elle requise ?", "Software Engineer", 4,
    "single_choice", ["Oui", "Non"])

# ── Data Scientist / Data Analyst ─────────────────────────────────────────────
for role in ["Data Scientist", "Data Analyst"]:
    make_q("Quel est le problème à résoudre avec les données ?", role, 1, "text")
    make_q("Quel est le volume de données disponibles ?", role, 2,
        "single_choice", ["Moins de 10 000 lignes", "10 000 à 1 million", "Plus de 1 million", "Données en streaming"])
    make_q("Les données sont-elles déjà collectées ?", role, 3,
        "single_choice", ["Oui — données prêtes", "Partiellement", "Non — à collecter"])
    make_q("Quel livrable est attendu ?", role, 4,
        "multi_choice", ["Dashboard interactif", "Rapport PDF / PowerPoint", "Modèle prédictif", "Pipeline de données", "API de données"])
    make_q("Quel outil de visualisation préférez-vous ?", role, 5,
        "single_choice", ["Power BI", "Tableau", "Looker / Google Data Studio", "Python (Plotly / Seaborn)", "Pas de préférence"])

# ── Machine Learning Engineer ─────────────────────────────────────────────────
q1 = make_q("Quel type de problème ML souhaitez-vous résoudre ?", "Machine Learning Engineer", 1,
    "single_choice", ["Classification", "Régression / Prédiction", "NLP (traitement du texte)", "Vision par ordinateur", "Recommandation", "Détection d anomalies"])
if q1:
    make_opts(q1, json.loads(q1.options))
    make_sub("Précisez le texte à traiter (langue, volume, source)", q1, "NLP", 1, "text")
    make_sub("Quel type d images / vidéos ? (ex: photos produits, radios...)", q1, "Vision", 1, "text")
make_q("Un déploiement du modèle est-il requis ?", "Machine Learning Engineer", 2,
    "single_choice", ["Oui — API REST", "Oui — intégré dans une app", "Oui — en batch / scheduled", "Non — recherche uniquement"])
make_q("Quelles données d entraînement avez-vous ?", "Machine Learning Engineer", 3,
    "single_choice", ["Données labellisées prêtes", "Données brutes à labelliser", "Pas de données — à collecter", "Utilisation de données publiques"])
make_q("L interprétabilité du modèle est-elle importante ?", "Machine Learning Engineer", 4,
    "single_choice", ["Oui — explication des décisions requise", "Non — seule la performance compte"])

# ── Cybersecurity Analyst ─────────────────────────────────────────────────────
q1 = make_q("Quel type d intervention cybersécurité souhaitez-vous ?", "Cybersecurity Analyst", 1,
    "multi_choice", ["Test d intrusion (Pentest)", "Audit de code sécurité", "Analyse de vulnérabilités", "Mise en conformité (RGPD, ISO 27001)", "Formation de l équipe"])
make_q("Quelle est la surface d attaque à tester ?", "Cybersecurity Analyst", 2,
    "multi_choice", ["Application web", "API / Services", "Infrastructure réseau", "Application mobile", "Phishing / Social engineering"])
make_q("Un rapport détaillé des vulnérabilités est-il requis ?", "Cybersecurity Analyst", 3,
    "single_choice", ["Oui — avec recommandations de correction", "Oui — résumé exécutif uniquement", "Non"])
make_q("Y a-t-il une norme de conformité visée ?", "Cybersecurity Analyst", 4,
    "single_choice", ["ISO 27001", "RGPD", "SOC 2", "PCI-DSS", "Aucune norme spécifique"])

# ── Database Administrator ────────────────────────────────────────────────────
make_q("Quel SGBD utilisez-vous ou souhaitez-vous utiliser ?", "Database Administrator (DBA)", 1,
    "single_choice", ["PostgreSQL", "MySQL / MariaDB", "Oracle", "SQL Server", "MongoDB", "Autre"])
make_q("Quel est le contexte de la mission ?", "Database Administrator (DBA)", 2,
    "single_choice", ["Nouvelle base de données", "Migration de base existante", "Optimisation des performances", "Maintenance et support"])
make_q("La haute disponibilité de la BDD est-elle requise ?", "Database Administrator (DBA)", 3,
    "single_choice", ["Oui — réplication / clustering", "Oui — sauvegardes automatiques seulement", "Non"])
make_q("Quel volume de données estimez-vous ?", "Database Administrator (DBA)", 4,
    "single_choice", ["Moins de 1 Go", "1 Go à 100 Go", "100 Go à 1 To", "Plus de 1 To"])

# ── QA Engineer ───────────────────────────────────────────────────────────────
make_q("Quel type de tests souhaitez-vous ?", "QA Engineer (Quality Assurance)\n", 1,
    "multi_choice", ["Tests fonctionnels manuels", "Tests automatisés (Selenium / Cypress)", "Tests de charge / performance", "Tests de régression", "Tests mobile"])
make_q("Avez-vous déjà un plan de test ou une stratégie QA ?", "QA Engineer (Quality Assurance)\n", 2,
    "single_choice", ["Oui — plan existant", "Non — à créer de zéro"])
make_q("Quel environnement de test est disponible ?", "QA Engineer (Quality Assurance)\n", 3,
    "single_choice", ["Environnement de staging dédié", "Environnement de développement uniquement", "Production (attention requise)", "Aucun — à mettre en place"])

# ─────────────────────────── DESIGN & CREATIVE ───────────────────────────────

# ── UI/UX Designer ────────────────────────────────────────────────────────────
q1 = make_q("Quel type de livrable UI/UX attendez-vous ?", "UI/UX Designer", 1,
    "single_choice", ["Wireframes (basse fidélité)", "Maquettes haute fidélité", "Prototype cliquable Figma", "Design system complet", "Tout (wireframe → prototype)"])
if q1:
    make_opts(q1, json.loads(q1.options))
    make_sub("Combien d écrans / pages faut-il prototyper ?", q1, "Prototype", 1, "text")
    make_sub("Combien de composants le design system doit-il inclure ?", q1, "Design system", 1, "text")

make_q("Une charte graphique existante doit-elle être respectée ?", "UI/UX Designer", 2,
    "single_choice", ["Oui — charte complète fournie", "Oui — logo + couleurs seulement", "Non — liberté créative"])
make_q("Des tests utilisateurs sont-ils inclus dans la prestation ?", "UI/UX Designer", 3,
    "single_choice", ["Oui — tests avec vrais utilisateurs", "Oui — tests heuristiques seulement", "Non"])
make_q("Sur quelle plateforme le design sera-t-il utilisé ?", "UI/UX Designer", 4,
    "multi_choice", ["Web (desktop)", "Web (mobile responsive)", "Application iOS", "Application Android", "Tablette"])
make_q("Quelles recherches utilisateurs souhaitez-vous ?", "UI/UX Designer", 5,
    "multi_choice", ["Interviews utilisateurs", "Persona et user journey", "Audit UX de l existant", "A/B testing", "Aucune"])

# ── Graphic Designer ──────────────────────────────────────────────────────────
q1 = make_q("Quel type de création graphique est attendu ?", "Graphic Designer", 1,
    "single_choice", ["Affiche / Flyer", "Brochure / Catalogue", "Infographie", "Bannières web / pub", "Packaging produit", "Autre"])
if q1:
    make_opts(q1, json.loads(q1.options))
    make_sub("Format papier souhaité ? (A4, A3, A5...)", q1, "Affiche", 1, "text")
    make_sub("Nombre de pages du catalogue ?", q1, "Catalogue", 1, "text")
make_q("Avez-vous une charte graphique existante ?", "Graphic Designer", 2,
    "single_choice", ["Oui — fournie", "Non — à créer", "Partiellement (logo seulement)"])
make_q("Format(s) de livraison attendus ?", "Graphic Designer", 3,
    "multi_choice", ["PDF (impression)", "PNG / JPG (web)", "Fichier source (AI, PSD)", "SVG (vectoriel)"])
make_q("Combien de révisions sont incluses dans votre budget ?", "Graphic Designer", 4,
    "single_choice", ["1 révision", "2 à 3 révisions", "Révisions illimitées"])

# ── Brand Identity Designer ───────────────────────────────────────────────────
make_q("Le nom de la marque est-il déjà défini ?", "Brand Identity Designer", 1,
    "single_choice", ["Oui — nom finalisé", "Non — à trouver", "En cours de réflexion"])
make_q("Quels éléments de l identité visuelle souhaitez-vous ?", "Brand Identity Designer", 2,
    "multi_choice", ["Logo principal", "Déclinaisons du logo", "Palette de couleurs", "Typographies", "Charte graphique complète (brand book)", "Templates (cartes de visite, entête email)"])
q3 = make_q("Votre secteur d activité et vos concurrents directs ?", "Brand Identity Designer", 3, "text")
make_q("Comment décririez-vous la personnalité de votre marque ?", "Brand Identity Designer", 4,
    "multi_choice", ["Sérieuse / Professionnelle", "Dynamique / Jeune", "Luxueuse / Premium", "Accessible / Friendly", "Innovante / Tech", "Naturelle / Éco-responsable"])
make_q("Avez-vous des références visuelles ou marques que vous aimez ?", "Brand Identity Designer", 5,
    "text", required=False)

# ── Illustrator ───────────────────────────────────────────────────────────────
make_q("Quel style d illustration souhaitez-vous ?", "Illustrator", 1,
    "single_choice", ["Réaliste", "Cartoon / Fun", "Minimaliste", "Ligne claire (flat)", "Aquarelle / Peint", "Pixel art"])
make_q("Combien d illustrations faut-il produire ?", "Illustrator", 2,
    "single_choice", ["1 à 3", "4 à 10", "11 à 30", "Plus de 30"])
make_q("Pour quel usage seront utilisées les illustrations ?", "Illustrator", 3,
    "multi_choice", ["Site web", "Réseaux sociaux", "Impression (livres, magazines)", "Application mobile", "Animations"])
make_q("Format de livraison souhaité ?", "Illustrator", 4,
    "multi_choice", ["PNG (fond transparent)", "SVG (vectoriel)", "JPG", "Fichier source (AI, PSD)"])
make_q("Les droits d utilisation commerciale sont-ils requis ?", "Illustrator", 5,
    "single_choice", ["Oui — droits exclusifs", "Oui — droits non-exclusifs", "Pas besoin (usage personnel)"])

# ── Logo Designer ─────────────────────────────────────────────────────────────
make_q("Quel style de logo vous correspond ?", "Logo Designer", 1,
    "multi_choice", ["Emblème (icône + texte)", "Lettermark (initiales)", "Wordmark (texte seul)", "Mascotte", "Abstrait / Géométrique"])
make_q("Quelle est votre palette de couleurs préférée ?", "Logo Designer", 2,
    "text", required=False)
make_q("Combien de concepts initiaux souhaitez-vous ?", "Logo Designer", 3,
    "single_choice", ["1 concept", "2 à 3 concepts", "4 à 5 concepts"])
make_q("Dans quels contextes sera utilisé le logo ?", "Logo Designer", 4,
    "multi_choice", ["Site web", "Impression", "Réseaux sociaux", "Signalétique / affichage", "Fond sombre et fond clair"])
make_q("Format(s) de livraison attendus ?", "Logo Designer", 5,
    "multi_choice", ["SVG (vectoriel)", "PNG (fond transparent)", "PDF", "Fichier source (AI / EPS)"])

# ─────────────────────────── MEDIA & VIDEO ───────────────────────────────────

# ── Video Editor ─────────────────────────────────────────────────────────────
q1 = make_q("Quel est le type de vidéo à monter ?", "Video Editor", 1,
    "single_choice", ["Vidéo corporate / institutionnelle", "Publicité / Spot commercial", "YouTube / Contenu créateur", "Événement (mariage, conférence…)", "Court-métrage / Film", "Formation / e-learning"])
if q1:
    make_opts(q1, json.loads(q1.options))
    make_sub("Combien de supports de formation faut-il monter ?", q1, "Formation", 1, "text")

make_q("Les rushes (footage) sont-ils fournis ?", "Video Editor", 2,
    "single_choice", ["Oui — tous les rushes fournis", "Oui — partiellement fournis", "Non — à tourner d abord"])
make_q("Format de rendu final ?", "Video Editor", 3,
    "multi_choice", ["1080p 16:9 (YouTube / Web)", "4K 16:9", "Vertical 9:16 (Stories / Reels)", "Carré 1:1 (Instagram)", "Multiple formats"])
make_q("Des sous-titres ou incrustations de texte sont-ils requis ?", "Video Editor", 4,
    "single_choice", ["Oui — sous-titres automatiques", "Oui — sous-titres manuels multilingues", "Oui — texte / titres graphiques seulement", "Non"])
q5 = make_q("De la musique ou une voix-off est-elle requise ?", "Video Editor", 5,
    "single_choice", ["Oui — musique fournie", "Oui — musique libre de droits", "Oui — voix-off à enregistrer", "Non"])
if q5:
    make_opts(q5, json.loads(q5.options))
    make_sub("Langue et ton de la voix-off (ex: Français formal, Arabe neutre…)", q5, "voix-off", 1, "text")

# ── Motion Graphics Artist ────────────────────────────────────────────────────
make_q("Quel type d animation est attendu ?", "Motion Graphics Artist", 1,
    "single_choice", ["Intro / Outro YouTube", "Explainer vidéo animée", "Infographie animée", "Transitions et overlays", "Logo animé", "Publicité animée"])
make_q("Quelle est la durée approximative de l animation ?", "Motion Graphics Artist", 2,
    "single_choice", ["Moins de 30 secondes", "30 secondes à 1 minute", "1 à 3 minutes", "Plus de 3 minutes"])
make_q("Un script ou storyboard est-il fourni ?", "Motion Graphics Artist", 3,
    "single_choice", ["Oui — script et storyboard fournis", "Oui — script seulement", "Non — à créer ensemble"])
make_q("La voix-off est-elle fournie ou à enregistrer ?", "Motion Graphics Artist", 4,
    "single_choice", ["Fournie (fichier audio)", "À enregistrer (non inclus)", "Pas de voix-off — musique seulement", "Aucun audio"])

# ── Videographer ──────────────────────────────────────────────────────────────
q1 = make_q("Quel est le type de tournage ?", "Videographer (Event/Corporate/Commercial)", 1,
    "single_choice", ["Événement (mariage, gala, conférence)", "Vidéo corporate / institutionnelle", "Spot publicitaire", "Interview / Témoignage", "Reportage / Documentaire"])
if q1:
    make_opts(q1, json.loads(q1.options))
    make_sub("Date et lieu de l événement ?", q1, "vénement", 1, "text")

make_q("Combien de caméras sont nécessaires ?", "Videographer (Event/Corporate/Commercial)", 2,
    "single_choice", ["1 caméra", "2 caméras", "3 caméras et plus"])
make_q("Quelle est la durée prévue du tournage ?", "Videographer (Event/Corporate/Commercial)", 3,
    "single_choice", ["Moins de 2 heures", "2 à 4 heures", "Une journée complète", "Plusieurs jours"])
make_q("Une prise de vue par drone est-elle souhaitée ?", "Videographer (Event/Corporate/Commercial)", 4,
    "single_choice", ["Oui", "Non"])
make_q("Le montage est-il inclus ou uniquement le tournage ?", "Videographer (Event/Corporate/Commercial)", 5,
    "single_choice", ["Tournage + montage complet", "Tournage uniquement", "Montage uniquement (rushes fournis)"])

# ── Storyboard Artist ─────────────────────────────────────────────────────────
make_q("Pour quel usage est destiné le storyboard ?", "Storyboard Artist", 1,
    "single_choice", ["Film / Publicité", "Animation", "Jeu vidéo", "Présentation / Pitch", "Autre"])
make_q("Combien de scènes / planches sont nécessaires ?", "Storyboard Artist", 2,
    "single_choice", ["Moins de 10 planches", "10 à 30 planches", "30 à 60 planches", "Plus de 60 planches"])
make_q("Niveau de finition souhaité ?", "Storyboard Artist", 3,
    "single_choice", ["Esquisses rapides (rough)", "Semi-finalisé", "Finalisé et détaillé en couleur"])
make_q("Le script ou brief créatif est-il fourni ?", "Storyboard Artist", 4,
    "single_choice", ["Oui — script complet", "Oui — brief résumé", "Non — à développer ensemble"])

# ── Sound Designer ────────────────────────────────────────────────────────────
make_q("Pour quel projet le sound design est-il destiné ?", "Sound Designer", 1,
    "single_choice", ["Jeu vidéo", "Film / Court-métrage", "Publicité / Spot radio", "Application mobile", "Podcast", "Autre"])
make_q("Type de contenu sonore requis ?", "Sound Designer", 2,
    "multi_choice", ["Musique originale", "Effets sonores (SFX)", "Ambiances / Musique d atmosphère", "Voix-off / Narration", "Jingle / Signature sonore"])
make_q("Durée approximative du contenu sonore ?", "Sound Designer", 3, "text")
make_q("Format de livraison souhaité ?", "Sound Designer", 4,
    "multi_choice", ["MP3", "WAV (qualité studio)", "FLAC", "Stems séparés (multipistes)"])

# ─────────────────────── WRITING & CONTENT ───────────────────────────────────

# ── Copywriter ────────────────────────────────────────────────────────────────
q1 = make_q("Pour quel support écrivez-vous ?", "Copywriter", 1,
    "single_choice", ["Site web (pages, landing page)", "Publicité (Google Ads, Meta Ads)", "Emails / Newsletter", "Réseaux sociaux", "Brochure / Flyer", "Script vidéo / podcast"])
if q1:
    make_opts(q1, json.loads(q1.options))
    make_sub("Combien de pages du site faut-il rédiger ?", q1, "Site web", 1, "text")
    make_sub("Combien d emails dans la séquence ?", q1, "Emails", 1, "text")
    make_sub("Combien de posts par semaine ?", q1, "Réseaux sociaux", 1, "text")

make_q("Quel ton doit avoir le contenu ?", "Copywriter", 2,
    "single_choice", ["Formel / Professionnel", "Décontracté / Conversationnel", "Persuasif / Commercial", "Inspirant / Motivant", "Humoristique"])
make_q("Le contenu doit-il être optimisé SEO ?", "Copywriter", 3,
    "single_choice", ["Oui — avec mots-clés ciblés fournis", "Oui — recherche de mots-clés incluse", "Non"])
make_q("Avez-vous une persona ou profil client cible ?", "Copywriter", 4,
    "single_choice", ["Oui — persona documenté fourni", "Oui — description informelle", "Non"])

# ── Content Writer / Blogger ──────────────────────────────────────────────────
make_q("Quel type de contenu faut-il produire ?", "Content Writer / Blogger", 1,
    "single_choice", ["Articles de blog SEO", "Études de cas", "Livres blancs (whitepapers)", "Guides pratiques", "Actualités / News"])
make_q("Quelle est la longueur cible des articles ?", "Content Writer / Blogger", 2,
    "single_choice", ["Court (500–800 mots)", "Moyen (800–1 500 mots)", "Long (1 500–3 000 mots)", "Très long (3 000 mots+)"])
make_q("A quelle fréquence le contenu doit-il être publié ?", "Content Writer / Blogger", 3,
    "single_choice", ["1 article par semaine", "2 à 3 par semaine", "1 par mois", "À la demande"])
make_q("Les visuels (images, infographies) sont-ils inclus ?", "Content Writer / Blogger", 4,
    "single_choice", ["Oui — inclus", "Non — texte uniquement", "Partiellement"])

# ── Technical Writer ──────────────────────────────────────────────────────────
make_q("Quel type de documentation faut-il rédiger ?", "Technical Writer", 1,
    "multi_choice", ["Manuel utilisateur", "Documentation API (Swagger/OpenAPI)", "Guide d installation / déploiement", "Politique de sécurité / RGPD", "Cahier des charges", "FAQ / Base de connaissances"])
make_q("Quel est le niveau technique des lecteurs ?", "Technical Writer", 2,
    "single_choice", ["Grand public (non-technique)", "Utilisateurs métier", "Développeurs / Ingénieurs", "Experts techniques"])
make_q("Quel format de livraison est attendu ?", "Technical Writer", 3,
    "multi_choice", ["Word / Google Docs", "PDF", "Confluence / Notion", "Markdown / GitHub", "HTML (site de doc)"])

# ── Scriptwriter ──────────────────────────────────────────────────────────────
make_q("Pour quel type de contenu écrit-on le script ?", "Scriptwriter (YouTube, Podcasts, Video)", 1,
    "single_choice", ["Vidéo YouTube", "Podcast", "Publicité vidéo", "Formation en ligne", "Discours / Présentation"])
make_q("Quelle est la durée cible du contenu final ?", "Scriptwriter (YouTube, Podcasts, Video)", 2,
    "single_choice", ["Moins de 2 minutes", "2 à 5 minutes", "5 à 15 minutes", "Plus de 15 minutes"])
make_q("Le script inclut-il des indications de mise en scène ?", "Scriptwriter (YouTube, Podcasts, Video)", 3,
    "single_choice", ["Oui — script + indications visuelles", "Non — texte pur seulement"])

# ─────────────────────────── MARKETING ──────────────────────────────────────

# ── Digital Marketing Specialist ─────────────────────────────────────────────
q1 = make_q("Quels canaux digitaux souhaitez-vous activer ?", "Digital Marketing Specialist", 1,
    "multi_choice", ["SEO (référencement naturel)", "SEA (Google Ads)", "Social Media Ads (Meta, TikTok)", "Email Marketing", "Marketing d influence", "Content Marketing"])
make_q("Quel est votre objectif principal ?", "Digital Marketing Specialist", 2,
    "single_choice", ["Notoriété de marque", "Génération de leads qualifiés", "Ventes directes (e-commerce)", "Rétention / Fidélisation", "Lancement de produit"])
make_q("Quelle est votre cible géographique ?", "Digital Marketing Specialist", 3,
    "single_choice", ["Local (ville / région)", "National", "MENA / Maghreb", "Europe", "International"])
make_q("Disposez-vous déjà d outils marketing (CRM, Analytics) ?", "Digital Marketing Specialist", 4,
    "multi_choice", ["Google Analytics / GA4", "HubSpot / Salesforce", "Mailchimp / Brevo", "Pixel Meta / TikTok Ads", "Aucun outil en place"])
make_q("Quel est votre budget mensuel marketing ?", "Digital Marketing Specialist", 5,
    "single_choice", ["Moins de 300 DT/mois", "300 à 1 000 DT/mois", "1 000 à 5 000 DT/mois", "Plus de 5 000 DT/mois"])

# ── Social Media Manager ─────────────────────────────────────────────────────
make_q("Sur quels réseaux sociaux voulez-vous être présent ?", "Social Media Manager", 1,
    "multi_choice", ["Facebook", "Instagram", "TikTok", "LinkedIn", "YouTube", "X (Twitter)"])
make_q("La création de contenu visuel est-elle incluse ?", "Social Media Manager", 2,
    "single_choice", ["Oui — photos + graphismes", "Oui — vidéos courtes (Reels/TikTok)", "Oui — tout type de contenu", "Non — contenu texte uniquement"])
make_q("La modération / community management est-elle incluse ?", "Social Media Manager", 3,
    "single_choice", ["Oui — réponse aux commentaires et DMs", "Non — publication uniquement"])
q4 = make_q("Des publicités payantes sont-elles prévues ?", "Social Media Manager", 4,
    "single_choice", ["Oui — Meta Ads", "Oui — TikTok Ads", "Oui — LinkedIn Ads", "Non"])
if q4:
    make_opts(q4, json.loads(q4.options))
    make_sub("Quel est le budget publicitaire mensuel ?", q4, "Ads", 1, "text")

# ── SEO Specialist ────────────────────────────────────────────────────────────
q1 = make_q("Quel est l objectif SEO principal ?", "SEO Specialist", 1,
    "single_choice", ["Améliorer le positionnement sur Google", "Augmenter le trafic organique", "Optimiser un site en reconstruction", "Démarrer le SEO d un nouveau site"])
make_q("Disposez-vous d un site web existant ?", "SEO Specialist", 2,
    "single_choice", ["Oui — site existant à optimiser", "Non — nouveau site"])
make_q("Un audit SEO complet est-il souhaité ?", "SEO Specialist", 3,
    "single_choice", ["Oui — audit technique + contenu + backlinks", "Oui — audit technique uniquement", "Non"])
make_q("La création de contenu SEO est-elle incluse ?", "SEO Specialist", 4,
    "single_choice", ["Oui — articles de blog SEO", "Oui — optimisation des pages existantes", "Non"])
make_q("Quelle est la cible géographique du référencement ?", "SEO Specialist", 5,
    "single_choice", ["Local", "National", "International (multilingue)"])

# ── Google Ads / PPC Specialist ───────────────────────────────────────────────
make_q("Sur quelle plateforme publicitaire souhaitez-vous lancer des campagnes ?", "Google Ads / PPC Specialist", 1,
    "multi_choice", ["Google Search Ads", "Google Display / YouTube Ads", "Meta Ads (Facebook / Instagram)", "LinkedIn Ads", "TikTok Ads"])
make_q("Quel est votre budget publicitaire mensuel (hors honoraires) ?", "Google Ads / PPC Specialist", 2,
    "single_choice", ["Moins de 300 DT", "300 à 1 000 DT", "1 000 à 5 000 DT", "Plus de 5 000 DT"])
make_q("Avez-vous déjà des comptes publicitaires existants ?", "Google Ads / PPC Specialist", 3,
    "single_choice", ["Oui — à reprendre / optimiser", "Non — à créer de zéro"])
make_q("Quelle est votre conversion cible ?", "Google Ads / PPC Specialist", 4,
    "single_choice", ["Appel téléphonique", "Formulaire de contact / lead", "Vente en ligne", "Téléchargement / Inscription", "Visite en magasin"])

# ─────────────────────────── FINANCE ─────────────────────────────────────────

# ── Accountant ────────────────────────────────────────────────────────────────
q1 = make_q("Quel type de prestation comptable souhaitez-vous ?", "Accountant", 1,
    "multi_choice", ["Tenue de comptabilité mensuelle", "Déclarations fiscales (TVA, IS…)", "Bilan annuel", "Paie et charges sociales", "Audit comptable"])
make_q("Quel logiciel comptable utilisez-vous ?", "Accountant", 2,
    "single_choice", ["Sage", "Ciel Compta", "QuickBooks", "Excel uniquement", "Aucun logiciel"])
make_q("Quel est le volume mensuel de transactions ?", "Accountant", 3,
    "single_choice", ["Moins de 50", "50 à 200", "200 à 500", "Plus de 500"])
make_q("Avez-vous des employés (gestion de la paie requise) ?", "Accountant", 4,
    "single_choice", ["Oui", "Non"])

# ── Expert comptable ──────────────────────────────────────────────────────────
make_q("Quel est le statut juridique de votre entreprise ?", "Expert comptable", 1,
    "single_choice", ["Auto-entrepreneur / Freelance", "SARL", "SA", "Association", "Autre"])
make_q("Quelles missions souhaitez-vous confier ?", "Expert comptable", 2,
    "multi_choice", ["Comptabilité et fiscalité", "Commissariat aux comptes", "Conseil en gestion", "Création d entreprise", "Transmission / Cession"])
make_q("Votre entreprise est-elle soumise à un audit obligatoire ?", "Expert comptable", 3,
    "single_choice", ["Oui", "Non", "Je ne sais pas"])

# ── Finance Manager ───────────────────────────────────────────────────────────
make_q("Quel est le besoin principal en finance ?", "Finance Manager", 1,
    "single_choice", ["Contrôle de gestion et reporting", "Planification budgétaire", "Levée de fonds / Financement", "Restructuration financière", "DAF externalisé"])
make_q("Disposez-vous d un ERP ou outil de gestion financière ?", "Finance Manager", 2,
    "single_choice", ["Oui — ERP en place (SAP, Odoo…)", "Oui — outil basique (Excel)", "Non"])
make_q("Quels rapports financiers souhaitez-vous recevoir ?", "Finance Manager", 3,
    "multi_choice", ["P&L mensuel", "Tableau de bord KPI", "Cash-flow prévisionnel", "Business plan", "Rapport pour investisseurs"])

# ── Trader ────────────────────────────────────────────────────────────────────
make_q("Sur quel marché souhaitez-vous trader ?", "Trader (Securities/Forex)", 1,
    "multi_choice", ["Forex (devises)", "Actions / ETF", "Crypto-monnaies", "Matières premières", "Options / Dérivés"])
make_q("Quel type de stratégie recherchez-vous ?", "Trader (Securities/Forex)", 2,
    "single_choice", ["Scalping (court terme)", "Day trading", "Swing trading", "Position trading (long terme)", "Conseil en allocation d actifs"])
make_q("Quel est votre niveau en trading ?", "Trader (Securities/Forex)", 3,
    "single_choice", ["Débutant", "Intermédiaire", "Avancé"])

# ─────────────────────────── commit ──────────────────────────────────────────
try:
    db.commit()
    total = db.query(models.Question).count()
    total_cond = db.query(models.QuestionCondition).count()
    print(f"\n✓ {total} questions seeded, {total_cond} conditions (sous-questions)")
    from sqlalchemy import func
    summary = (db.query(models.Category.name, func.count(models.Question.id))
               .join(models.Question, models.Question.category_id == models.Category.id)
               .group_by(models.Category.name)
               .order_by(func.count(models.Question.id).desc()).all())
    for name, count in summary:
        print(f"  {count:2d}  {name}")
except Exception as e:
    db.rollback()
    import traceback; traceback.print_exc()
finally:
    db.close()
