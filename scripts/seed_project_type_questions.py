"""
Seed project-type-specific questions with multiple-choice options and sub-question chains.
Run from projet_pfe2 root:
    venv\\Scripts\\python.exe -m scripts.seed_project_type_questions
"""
import sys, uuid, json
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.core import models

db = SessionLocal()

# ── helpers ─────────────────────────────────────────────────────────────────

def get_project_type(name: str):
    row = db.query(models.ProjectType).filter(
        models.ProjectType.name == name,
        models.ProjectType.status == "active"
    ).first()
    if not row:
        print(f"  [SKIP] Project type not found: {name}")
    return row

def get_category(name: str):
    row = db.query(models.Category).filter(models.Category.name == name).first()
    if not row:
        print(f"  [WARN] Category not found: {name}")
    return row

def make_question(label, category, order, atype="single_choice",
                  options=None, required=True, project_type=None, description=None):
    q = models.Question(
        id=uuid.uuid4(),
        label=label,
        description=description,
        answer_type=atype,
        options=json.dumps(options) if options else None,
        is_required=required,
        display_order=order,
        status="active",
        category_id=category.id,
        project_type_id=project_type.id if project_type else None,
    )
    db.add(q)
    db.flush()

    # Create QuestionOption rows for choice types
    if options and atype in ("single_choice", "multi_choice", "boolean"):
        for i, opt_text in enumerate(options):
            db.add(models.QuestionOption(
                id=uuid.uuid4(),
                question_id=q.id,
                option_text=opt_text,
                display_order=i + 1
            ))
        db.flush()

    return q

def make_sub(label, parent_q, trigger_option_text=None, order=1,
             atype="text", options=None, required=False, description=None):
    """Sub-question shown when parent answer matches trigger_option_text."""
    q = models.Question(
        id=uuid.uuid4(),
        label=label,
        description=description,
        answer_type=atype,
        options=json.dumps(options) if options else None,
        is_required=required,
        display_order=order,
        status="active",
        category_id=parent_q.category_id,
        project_type_id=parent_q.project_type_id,
        parent_question_id=parent_q.id,
    )
    db.add(q)
    db.flush()

    # Create options rows
    if options and atype in ("single_choice", "multi_choice", "boolean"):
        for i, opt_text in enumerate(options):
            db.add(models.QuestionOption(
                id=uuid.uuid4(),
                question_id=q.id,
                option_text=opt_text,
                display_order=i + 1
            ))
        db.flush()

    # Wire QuestionCondition
    trigger_opt = None
    if trigger_option_text:
        trigger_opt = db.query(models.QuestionOption).filter_by(
            question_id=parent_q.id,
            option_text=trigger_option_text
        ).first()

    db.add(models.QuestionCondition(
        id=uuid.uuid4(),
        question_id=q.id,
        trigger_question_id=parent_q.id,
        trigger_option_id=trigger_opt.id if trigger_opt else None,
        trigger_value=None if trigger_opt else trigger_option_text,
        trigger_value_operator="contains",
        logical_operator="OR",
        priority=1,
        is_required=required,
    ))
    db.flush()
    return q


# ── GENERAL CATEGORY: upgrade budget + deadline from TEXT to single_choice ────

print("Updating general questions...")
general_cat = get_category("Informations Generales")

if general_cat:
    # Archive old text-based budget and deadline questions, add choice versions
    old_budget = db.query(models.Question).filter(
        models.Question.category_id == general_cat.id,
        models.Question.label.ilike("%budget%"),
        models.Question.answer_type == "text"
    ).first()
    old_deadline = db.query(models.Question).filter(
        models.Question.category_id == general_cat.id,
        models.Question.label.ilike("%delai%"),
        models.Question.answer_type == "text"
    ).first()

    if old_budget:
        old_budget.status = "archived"
    if old_deadline:
        old_deadline.status = "archived"
    db.flush()

    make_question(
        "Budget estimé pour ce projet",
        general_cat, 4,
        atype="single_choice",
        options=["Moins de 500 DT", "500 – 2 000 DT", "2 000 – 8 000 DT",
                 "8 000 – 20 000 DT", "Plus de 20 000 DT", "À définir ensemble"],
        required=False,
        description="Sélectionnez la fourchette de budget approximative."
    )
    make_question(
        "Délai souhaité de livraison",
        general_cat, 5,
        atype="single_choice",
        options=["Urgent (< 1 semaine)", "Court terme (1–4 semaines)",
                 "Moyen terme (1–3 mois)", "Long terme (3–6 mois)", "Flexible"],
        required=False,
        description="Quand souhaitez-vous recevoir le livrable ?"
    )
    print("  General questions updated.")


# ═══════════════════════════════════════════════════════════════════════════════
# INFORMATION TECHNOLOGY (IT)
# ═══════════════════════════════════════════════════════════════════════════════

print("\nSeeding IT questions...")
it = get_project_type("Information Technology (IT)")
it_cat = get_category("Software Engineer")  # use as anchor category for IT seed questions

if it and it_cat:
    # Seed Q1 — type of IT solution
    q_it_type = make_question(
        "Quel type de solution IT recherchez-vous ?",
        it_cat, 1,
        atype="single_choice",
        options=["Application Web", "Application Mobile", "API / Back-End",
                 "Solution Cloud / DevOps", "Data / Analytics / IA",
                 "Cybersécurité", "Autre"],
        required=True,
        project_type=it,
        description="Sélectionnez la nature principale de votre projet IT."
    )

    # Web branch
    q_web = make_sub("Quel type d'application web ?", q_it_type,
                     trigger_option_text="Application Web", order=1,
                     atype="single_choice",
                     options=["Site vitrine / présentation", "E-commerce", "SaaS / plateforme",
                              "Application métier interne", "Blog / CMS", "Portail communautaire"])
    make_sub("Avez-vous déjà une charte graphique / maquettes ?", q_web,
             trigger_option_text=None, order=2,
             atype="single_choice", options=["Oui, prêtes", "Partiellement", "Non, à créer"])
    make_sub("Quel framework front-end préférez-vous ?", q_web,
             trigger_option_text=None, order=3,
             atype="single_choice",
             options=["React", "Vue.js", "Angular", "Svelte", "Pas de préférence"])

    # Mobile branch
    q_mobile = make_sub("Quelle plateforme mobile ciblez-vous ?", q_it_type,
                        trigger_option_text="Application Mobile", order=1,
                        atype="single_choice",
                        options=["iOS uniquement", "Android uniquement",
                                 "Les deux (React Native / Flutter)", "Progressive Web App (PWA)"])
    make_sub("L'application nécessite-t-elle un fonctionnement hors-ligne ?", q_mobile,
             trigger_option_text=None, order=2,
             atype="single_choice", options=["Oui", "Non", "Partiellement"])
    make_sub("Des notifications push sont-elles requises ?", q_mobile,
             trigger_option_text=None, order=3,
             atype="single_choice", options=["Oui", "Non"])

    # API branch
    q_api = make_sub("Quel type d'API / back-end recherchez-vous ?", q_it_type,
                     trigger_option_text="API / Back-End", order=1,
                     atype="single_choice",
                     options=["REST API", "GraphQL", "Microservices", "Temps réel (WebSocket)"])
    make_sub("Quel langage / framework back-end préférez-vous ?", q_api,
             trigger_option_text=None, order=2,
             atype="single_choice",
             options=["Python (FastAPI / Django)", "Node.js (Express)", "Java (Spring)", "PHP (Laravel)", "Pas de préférence"])
    make_sub("Quel type de base de données ?", q_api,
             trigger_option_text=None, order=3,
             atype="single_choice",
             options=["SQL (PostgreSQL, MySQL)", "NoSQL (MongoDB, Redis)", "Les deux", "Pas de préférence"])

    # Data / IA branch
    q_data = make_sub("Quel domaine Data / IA vous intéresse ?", q_it_type,
                      trigger_option_text="Data / Analytics / IA", order=1,
                      atype="multi_choice",
                      options=["Tableau de bord / reporting", "Machine Learning",
                               "NLP / traitement du texte", "Computer Vision",
                               "Pipeline de données (ETL)", "Analyse prédictive"])
    make_sub("Avez-vous déjà des données disponibles ?", q_data,
             trigger_option_text=None, order=2,
             atype="single_choice", options=["Oui, structurées", "Oui, non structurées", "Non, à collecter"])

    # Cloud branch
    make_sub("Quel fournisseur cloud préférez-vous ?", q_it_type,
             trigger_option_text="Solution Cloud / DevOps", order=1,
             atype="single_choice",
             options=["AWS", "Google Cloud", "Azure", "OVH / Hetzner", "Pas de préférence"])

    # Seed Q2 — authentication
    make_question(
        "Un système d'authentification utilisateur est-il nécessaire ?",
        it_cat, 2,
        atype="single_choice",
        options=["Oui — login / mot de passe", "Oui — OAuth (Google, GitHub…)",
                 "Oui — double facteur (2FA)", "Non"],
        required=False,
        project_type=it,
    )

    # Seed Q3 — existing codebase
    q_existing = make_question(
        "Partez-vous d'un projet existant ou d'une base de code vierge ?",
        it_cat, 3,
        atype="single_choice",
        options=["Projet existant à reprendre / améliorer",
                 "Partir de zéro (greenfield)",
                 "Migration depuis une autre technologie"],
        required=False,
        project_type=it,
    )
    make_sub("Quel(s) langage(s) / technologie(s) utilise le projet existant ?",
             q_existing, trigger_option_text="Projet existant à reprendre / améliorer",
             order=1, atype="text")
    make_sub("Depuis quelle technologie migrez-vous ?", q_existing,
             trigger_option_text="Migration depuis une autre technologie",
             order=1, atype="text")

    print("  IT questions seeded.")


# ═══════════════════════════════════════════════════════════════════════════════
# GAME DEVELOPMENT & 3D MODELING
# ═══════════════════════════════════════════════════════════════════════════════

print("\nSeeding Game Development questions...")
game = get_project_type("Game Development & 3D Modeling")
game_cat = get_category("Game Designer")

if game and game_cat:
    q_game_type = make_question(
        "Quel type de projet jeu / 3D développez-vous ?",
        game_cat, 1,
        atype="single_choice",
        options=["Jeu vidéo", "Application VR / AR", "Film d'animation 3D",
                 "Visualisation architecturale / produit", "Simulation", "Autre"],
        required=True,
        project_type=game,
        description="Définissez la nature principale de votre projet."
    )

    # Jeu vidéo branch
    q_genre = make_sub("Quel genre de jeu ?", q_game_type,
                       trigger_option_text="Jeu vidéo", order=1,
                       atype="single_choice",
                       options=["Action / Aventure", "RPG", "Puzzle / Casual",
                                "Sport / Course", "Stratégie", "Platformer", "Horreur / Survie"])
    make_sub("Quelle(s) plateforme(s) ciblez-vous ?", q_genre,
             trigger_option_text=None, order=2,
             atype="multi_choice",
             options=["PC (Windows / Mac)", "Console PlayStation", "Console Xbox",
                      "Nintendo Switch", "Mobile (iOS / Android)", "Web (navigateur)"])
    make_sub("Quel moteur de jeu préférez-vous ?", q_genre,
             trigger_option_text=None, order=3,
             atype="single_choice",
             options=["Unity", "Unreal Engine", "Godot", "Pas de préférence"])

    # VR/AR branch
    q_vr = make_sub("Quel dispositif VR / AR visez-vous ?", q_game_type,
                    trigger_option_text="Application VR / AR", order=1,
                    atype="single_choice",
                    options=["Meta Quest (standalone)", "PC VR (HTC Vive, Valve Index)",
                             "PlayStation VR", "Lunettes AR (HoloLens, Magic Leap)",
                             "Smartphone AR (ARKit / ARCore)"])
    make_sub("L'expérience VR/AR est-elle multi-joueurs ?", q_vr,
             trigger_option_text=None, order=2,
             atype="single_choice", options=["Oui", "Non"])

    # 3D Film branch
    make_sub("Quel logiciel 3D utilisez-vous (ou souhaitez-vous utiliser) ?",
             q_game_type, trigger_option_text="Film d'animation 3D", order=1,
             atype="single_choice",
             options=["Blender", "Maya", "Cinema 4D", "3ds Max", "Pas de préférence"])

    q_game_multi = make_question(
        "Le jeu / projet inclut-il un mode multijoueur ?",
        game_cat, 2,
        atype="single_choice",
        options=["Oui — en ligne", "Oui — local (même écran / réseau LAN)", "Non"],
        required=False,
        project_type=game,
    )
    make_sub("Combien de joueurs simultanés attendez-vous ?", q_game_multi,
             trigger_option_text="Oui — en ligne", order=1,
             atype="single_choice",
             options=["2–4 joueurs", "5–20 joueurs", "21–100 joueurs", "100+ joueurs (MMO)"])

    make_question(
        "Avez-vous déjà des assets (modèles 3D, sons, illustrations) ?",
        game_cat, 3,
        atype="single_choice",
        options=["Oui, la plupart sont prêts", "Partiellement", "Non, tout est à créer"],
        required=False,
        project_type=game,
    )
    print("  Game Development questions seeded.")


# ═══════════════════════════════════════════════════════════════════════════════
# DESIGN & CREATIVE
# ═══════════════════════════════════════════════════════════════════════════════

print("\nSeeding Design questions...")
design = get_project_type("Design & Creative")
design_cat = get_category("Graphic Designer")

if design and design_cat:
    q_design_type = make_question(
        "Quel type de création design recherchez-vous ?",
        design_cat, 1,
        atype="single_choice",
        options=["Identité visuelle / Logo", "Design UI/UX (application / site)",
                 "Motion Design / Animation", "Illustration",
                 "Design print (affiche, brochure, packaging)", "Autre"],
        required=True,
        project_type=design,
        description="Sélectionnez la prestation design principale."
    )

    # Logo branch
    q_logo = make_sub("Avez-vous déjà une direction artistique ou références visuelles ?",
                      q_design_type, trigger_option_text="Identité visuelle / Logo",
                      order=1, atype="single_choice",
                      options=["Oui, avec références précises", "Quelques idées", "Non, carte blanche"])
    make_sub("Quels supports utiliseront ce logo / identité ?",
             q_logo, trigger_option_text=None, order=2,
             atype="multi_choice",
             options=["Web / réseaux sociaux", "Impression (cartes, brochures)",
                      "Signalétique / enseignes", "Vêtements / goodies", "Vidéo / animations"])

    # UI/UX branch
    q_ux = make_sub("Quel type de produit digital à designer ?",
                    q_design_type, trigger_option_text="Design UI/UX (application / site)",
                    order=1, atype="single_choice",
                    options=["Application mobile", "Application web / SaaS",
                             "Site vitrine", "Dashboard / back-office", "E-commerce"])
    make_sub("Livrez-vous des maquettes interactives (prototype) ?",
             q_ux, trigger_option_text=None, order=2,
             atype="single_choice", options=["Oui (Figma / Adobe XD)", "Non, images statiques"])

    # Motion branch
    make_sub("Quelle durée approximative pour l'animation ?",
             q_design_type, trigger_option_text="Motion Design / Animation",
             order=1, atype="single_choice",
             options=["< 15 secondes", "15–60 secondes", "1–3 minutes", "> 3 minutes"])

    make_question(
        "Avez-vous une charte graphique existante (couleurs, typographie) ?",
        design_cat, 2,
        atype="single_choice",
        options=["Oui, à respecter strictement", "Oui, mais peut évoluer", "Non"],
        required=False,
        project_type=design,
    )
    print("  Design questions seeded.")


# ═══════════════════════════════════════════════════════════════════════════════
# MARKETING & ADVERTISING
# ═══════════════════════════════════════════════════════════════════════════════

print("\nSeeding Marketing questions...")
marketing = get_project_type("Marketing & Advertising")
mkt_cat = get_category("Digital Marketing Specialist")

if marketing and mkt_cat:
    q_mkt_type = make_question(
        "Quel type de campagne / stratégie marketing planifiez-vous ?",
        mkt_cat, 1,
        atype="single_choice",
        options=["Réseaux sociaux (organique)", "Publicité payante (Google / Meta Ads)",
                 "SEO / Marketing de contenu", "Email marketing / automation",
                 "Influence / partenariats", "Stratégie globale multi-canal"],
        required=True,
        project_type=marketing,
        description="Sélectionnez l'axe principal de votre projet marketing."
    )

    q_social = make_sub("Sur quels réseaux sociaux souhaitez-vous intervenir ?",
                        q_mkt_type, trigger_option_text="Réseaux sociaux (organique)",
                        order=1, atype="multi_choice",
                        options=["Instagram", "Facebook", "LinkedIn", "TikTok",
                                 "YouTube", "X (Twitter)", "Pinterest"])
    make_sub("Avez-vous déjà des comptes actifs sur ces réseaux ?",
             q_social, trigger_option_text=None, order=2,
             atype="single_choice", options=["Oui", "Non", "Partiellement"])

    make_sub("Quel budget publicitaire mensuel prévoyez-vous ?",
             q_mkt_type, trigger_option_text="Publicité payante (Google / Meta Ads)",
             order=1, atype="single_choice",
             options=["< 500 DT / mois", "500–2 000 DT / mois",
                      "2 000–10 000 DT / mois", "> 10 000 DT / mois"])

    make_sub("Sur quels mots-clés ou thématiques souhaitez-vous vous positionner ?",
             q_mkt_type, trigger_option_text="SEO / Marketing de contenu",
             order=1, atype="text", required=False)

    make_question(
        "Avez-vous déjà un site web ou une présence en ligne ?",
        mkt_cat, 2,
        atype="single_choice",
        options=["Oui, site web actif", "Oui, réseaux sociaux uniquement",
                 "Non, à créer"],
        required=False,
        project_type=marketing,
    )

    make_question(
        "Quelle est votre cible client principale ?",
        mkt_cat, 3,
        atype="single_choice",
        options=["B2C (grand public)", "B2B (entreprises)", "B2B2C", "Mixte"],
        required=True,
        project_type=marketing,
    )
    print("  Marketing questions seeded.")


# ═══════════════════════════════════════════════════════════════════════════════
# MEDIA & VIDEO PRODUCTION
# ═══════════════════════════════════════════════════════════════════════════════

print("\nSeeding Media & Video questions...")
media = get_project_type("Media & Video Production")
media_cat = get_category("Videographer (Event/Corporate/Commercial)")

if media and media_cat:
    q_video_type = make_question(
        "Quel type de production vidéo recherchez-vous ?",
        media_cat, 1,
        atype="single_choice",
        options=["Publicité / spot commercial", "Vidéo d'entreprise / corporate",
                 "Contenu YouTube / réseaux sociaux", "Couverture d'événement",
                 "Documentaire", "Formation / e-learning", "Animation / motion design"],
        required=True,
        project_type=media,
        description="Définissez le format de production souhaité."
    )

    make_sub("Quelle durée approximative pour la vidéo ?",
             q_video_type, trigger_option_text=None, order=1,
             atype="single_choice",
             options=["< 1 minute", "1–3 minutes", "3–10 minutes",
                      "10–30 minutes", "> 30 minutes"])

    make_sub("Avez-vous besoin d'un script / scénario ?",
             q_video_type, trigger_option_text=None, order=2,
             atype="single_choice", options=["Oui, à écrire", "Oui, j'ai déjà un script", "Non"])

    make_question(
        "La vidéo nécessite-t-elle de la voix off ou des sous-titres ?",
        media_cat, 2,
        atype="multi_choice",
        options=["Voix off", "Sous-titres français", "Sous-titres anglais",
                 "Traduction / doublage", "Aucun de ces éléments"],
        required=False,
        project_type=media,
    )

    make_question(
        "Où sera diffusée la vidéo ?",
        media_cat, 3,
        atype="multi_choice",
        options=["YouTube", "Instagram / TikTok", "LinkedIn",
                 "Site web", "TV / affichage public", "Interne (formation, réunion)"],
        required=False,
        project_type=media,
    )
    print("  Media & Video questions seeded.")


# ═══════════════════════════════════════════════════════════════════════════════
# WRITING & CONTENT CREATION
# ═══════════════════════════════════════════════════════════════════════════════

print("\nSeeding Writing questions...")
writing = get_project_type("Writing & Content Creation")
writing_cat = get_category("Content Writer / Blogger")

if writing and writing_cat:
    q_content_type = make_question(
        "Quel type de contenu écrit recherchez-vous ?",
        writing_cat, 1,
        atype="single_choice",
        options=["Articles de blog / SEO", "Copywriting commercial (pub, landing page)",
                 "Contenu réseaux sociaux", "Script vidéo / podcast",
                 "Documentation technique", "Roman / fiction", "Traduction"],
        required=True,
        project_type=writing,
        description="Sélectionnez le type de livrable attendu."
    )

    make_sub("Combien d'articles / publications sont attendus ?",
             q_content_type, trigger_option_text="Articles de blog / SEO",
             order=1, atype="single_choice",
             options=["1 article", "2–5 articles", "6–15 articles", "15+ articles (abonnement)"])
    make_sub("Avez-vous des mots-clés SEO cibles ?",
             q_content_type, trigger_option_text="Articles de blog / SEO",
             order=2, atype="single_choice", options=["Oui", "Non, à définir ensemble"])

    make_sub("Pour quelle plateforme le script est-il destiné ?",
             q_content_type, trigger_option_text="Script vidéo / podcast",
             order=1, atype="single_choice",
             options=["YouTube", "Podcast audio", "Formation e-learning",
                      "Publicité vidéo", "Présentation / webinaire"])

    make_question(
        "Quelle est la langue principale du contenu ?",
        writing_cat, 2,
        atype="single_choice",
        options=["Français", "Anglais", "Arabe", "Bilingue (FR + EN)",
                 "Autre"],
        required=True,
        project_type=writing,
    )

    make_question(
        "Avez-vous un guide de style ou une ligne éditoriale définie ?",
        writing_cat, 3,
        atype="single_choice",
        options=["Oui, document disponible", "Partiellement", "Non"],
        required=False,
        project_type=writing,
    )
    print("  Writing questions seeded.")


# ═══════════════════════════════════════════════════════════════════════════════
# FINANCE
# ═══════════════════════════════════════════════════════════════════════════════

print("\nSeeding Finance questions...")
finance = get_project_type("Finance")
finance_cat = get_category("Accountant")

if finance and finance_cat:
    q_finance_type = make_question(
        "Quel type de service financier recherchez-vous ?",
        finance_cat, 1,
        atype="single_choice",
        options=["Comptabilité courante", "Audit & révision des comptes",
                 "Analyse financière / business plan", "Déclaration fiscale",
                 "Conseil en investissement / trading", "Gestion de paie"],
        required=True,
        project_type=finance,
        description="Sélectionnez la nature principale du service financier."
    )

    make_sub("Votre entreprise est-elle soumise à la TVA ?",
             q_finance_type, trigger_option_text="Comptabilité courante",
             order=1, atype="single_choice", options=["Oui", "Non", "Je ne sais pas"])
    make_sub("Quel logiciel comptable utilisez-vous actuellement ?",
             q_finance_type, trigger_option_text="Comptabilité courante",
             order=2, atype="single_choice",
             options=["Sage", "Odoo", "QuickBooks", "Excel / manuel", "Aucun"])

    make_sub("À quel stade en êtes-vous dans votre business plan ?",
             q_finance_type, trigger_option_text="Analyse financière / business plan",
             order=1, atype="single_choice",
             options=["Idée / concept", "Projet en cours", "Recherche de financement",
                      "Développement / lancement"])

    make_question(
        "Quelle est la taille de votre structure ?",
        finance_cat, 2,
        atype="single_choice",
        options=["Auto-entrepreneur / freelance", "TPE (1–9 employés)",
                 "PME (10–250 employés)", "Grande entreprise (250+)"],
        required=False,
        project_type=finance,
    )
    print("  Finance questions seeded.")


# ── commit ────────────────────────────────────────────────────────────────────
db.commit()
db.close()
print("\nDone. All project-type-specific questions seeded successfully.")
