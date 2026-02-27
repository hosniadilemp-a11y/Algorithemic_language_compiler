import os
import sys

# Define absolute paths to ensure imports work from this script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.append(BASE_DIR)

from app import app, db
from models import Chapter, Question, Choice

def seed_chapter_1():
    with app.app_context():
        # Clean existing data for idempotency
        db.drop_all()
        db.create_all()

        print("Base de données initialisée.")

        # Create Chapter
        ch1 = Chapter(title="Chapitre 1: Introduction à l'Algorithmique", identifier="intro")
        db.session.add(ch1)
        db.session.commit()

        print("Ajout des questions pour le Chapitre 1...")

        questions_data = [
            # EASY (Concepts de base, variables, types)
            {
                "type": "MCQ", "difficulty": "Easy", "concept": "Définition",
                "text": "Qu'est-ce qu'un algorithme au sens strict ?",
                "explanation": "Un algorithme est une suite finie et précise d'instructions. Ce n'est pas le code lui-même (qui dépend du langage), ni juste une idée vague.",
                "choices": [
                    ("Une suite finie d'instructions pour résoudre un problème", True),
                    ("Un programme informatique écrit en C ou Python", False),
                    ("Une liste de souhaits non ordonnée", False),
                    ("Un composant matériel de l'ordinateur", False)
                ]
            },
            {
                "type": "TrueFalse", "difficulty": "Easy", "concept": "Définition",
                "text": "Une recette de cuisine est un exemple d'algorithme dans la vie réelle.",
                "explanation": "Vrai. Elle comprend des entrées (ingrédients), des instructions précises (étapes), et une sortie (le plat).",
                "choices": [("Vrai", True), ("Faux", False)]
            },
            {
                "type": "MCQ", "difficulty": "Easy", "concept": "Variables",
                "text": "Que représente concrètement une 'Variable' ?",
                "explanation": "Une variable agit comme un tiroir dans la RAM avec une étiquette (le nom) et un contenu (la valeur).",
                "choices": [
                    ("Un espace nommé dans la mémoire (RAM) pour stocker une valeur", True),
                    ("Une instruction qui répète une action", False),
                    ("Un nombre qui ne change jamais", False),
                    ("Le disque dur de l'ordinateur", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Easy", "concept": "Types",
                "text": "Quel type de donnée utiliseriez-vous pour stocker l'âge d'une personne ?",
                "explanation": "L'âge est un nombre entier (ex: 18, 45). On n'utilise pas de virgule pour un âge typique.",
                "choices": [
                    ("Entier", True),
                    ("Reel", False),
                    ("Chaine", False),
                    ("Booleen", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Easy", "concept": "Affectation",
                "text": "Que fait l'instruction `A := 5` ?",
                "explanation": "L'opérateur `:=` est l'affectation. Il place la valeur située à droite dans la variable située à gauche.",
                "choices": [
                    ("Elle place la valeur 5 dans la variable A", True),
                    ("Elle vérifie si A est égal à 5", False),
                    ("Elle ajoute 5 à la variable A", False),
                    ("Elle affiche le chiffre 5 à l'écran", False)
                ]
            },
            {
                "type": "TrueFalse", "difficulty": "Easy", "concept": "Variables",
                "text": "Il est possible de changer la valeur d'une CONSTANTE au milieu de l'algorithme.",
                "explanation": "Faux. Par définition, une constante est verrouillée dès sa déclaration et ne peut plus être modifiée.",
                "choices": [("Vrai", False), ("Faux", True)]
            },

            # MEDIUM (Logique, opérateurs, boucles simples)
            {
                "type": "MCQ", "difficulty": "Medium", "concept": "Opérateurs",
                "text": "Quel est le résultat de l'opération `10 % 3` (10 modulo 3) ?",
                "explanation": "Le modulo (%) donne le reste de la division entière. 10 divisé par 3 fait 3, et il reste 1.",
                "choices": [
                    ("1", True), ("3.33", False), ("3", False), ("0", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Medium", "concept": "Logique",
                "text": "Si `A = Vrai` et `B = Faux`, quelle est la valeur de l'expression `(A Ou B)` ?",
                "explanation": "L'opérateur 'Ou' retourne Vrai si au moins l'une des deux conditions est Vraie. Ici, A est Vrai.",
                "choices": [
                    ("Vrai", True), ("Faux", False), ("Erreur", False), ("NIL", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Medium", "concept": "Logique",
                "text": "Si `A = Vrai` et `B = Faux`, quelle est la valeur de l'expression `(A Et B)` ?",
                "explanation": "L'opérateur 'Et' exige que TOUTES les conditions soient Vraies. Ici, B étant Faux, l'ensemble est Faux.",
                "choices": [
                    ("Faux", True), ("Vrai", False), ("Erreur", False), ("NIL", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Medium", "concept": "Affectation",
                "text": "Si `X = 10` et `Y = 20`. Après l'instruction `X := Y`, que valent X et Y ?",
                "explanation": "La valeur de Y (20) est copiée dans X. Y conserve sa valeur. Donc les deux valent 20.",
                "choices": [
                    ("X = 20, Y = 20", True),
                    ("X = 10, Y = 20", False),
                    ("X = 20, Y = 10", False),
                    ("X = 0, Y = 0", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Medium", "concept": "Conditions",
                "text": "Dans une structure `Si... Alors... Sinon`, quand le bloc `Sinon` est-il exécuté ?",
                "explanation": "Le bloc `Sinon` est l'alternative exécutée uniquement si la condition initiale testée dans le `Si` est évaluée à Faux.",
                "choices": [
                    ("Quand la condition du Si est Fausse", True),
                    ("Quand la condition du Si est Vraie", False),
                    ("Toujours, à la fin du Si", False),
                    ("Au hasard", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Medium", "concept": "Boucles",
                "text": "Laquelle de ces boucles exécute SON BLOC d'instructions TOUJOURS AU MOINS UNE FOIS, peu importe la condition ?",
                "explanation": "La boucle `Repeter... Jusqua` teste sa condition à la fin de la boucle. Le code à l'intérieur est donc lu au moins une fois avant le premier test.",
                "choices": [
                    ("Repeter ... Jusqua", True),
                    ("TantQue ... Faire", False),
                    ("Pour ... Faire", False),
                    ("Si ... Alors", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Medium", "concept": "Boucles",
                "text": "Si je sais exactement que je dois afficher 5 fois le mot 'Bonjour', quelle boucle est la plus appropriée ?",
                "explanation": "La boucle `Pour` est conçue spécifiquement pour les itérations dont le nombre exact est connu à l'avance (ex: de 1 à 5).",
                "choices": [
                    ("Pour", True),
                    ("TantQue", False),
                    ("Repeter", False),
                    ("Si", False)
                ]
            },
            {
                "type": "TrueFalse", "difficulty": "Medium", "concept": "Types",
                "text": "Le type 'Chaine' consomme généralement moins de mémoire que le type 'Booleen'.",
                "explanation": "Faux. Un Booleen tient souvent sur 1 octet (voire 1 bit). Une Chaîne occupe au moins 1 octet *par caractère*.",
                "choices": [("Vrai", False), ("Faux", True)]
            },

            # HARD (Swap complexe, traces d'algo, conditions imbriquées)
            {
                "type": "MCQ", "difficulty": "Hard", "concept": "Algorithmique",
                "text": "Pour échanger les valeurs de A et B en utilisant une variable temporaire 'T', quel est le bon ordre d'instructions ?",
                "explanation": "On sauvegarde A dans T, puis on écrase A avec B, et enfin on met dans B l'ancienne valeur de A sauvegardée dans T.",
                "choices": [
                    ("T:=A; A:=B; B:=T;", True),
                    ("A:=T; T:=B; B:=A;", False),
                    ("A:=B; B:=T; T:=A;", False),
                    ("T:=B; B:=A; A:=T;", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Hard", "concept": "Algorithmique",
                "text": "Tracez cet algorithme brèf : `A:=5; B:=10; A:=A+B; B:=A-B; A:=A-B;`. Que se passe-t-il ?",
                "explanation": "C'est la méthode mathématique pour inverser deux variables (Swap) sans utiliser de variable temporelle. À la fin, A=10 et B=5.",
                "choices": [
                    ("Les valeurs de A et B sont échangées (A=10, B=5)", True),
                    ("A devient 15 et B devient 0", False),
                    ("A devient 5 et B devient 10 (rien ne change)", False),
                    ("C'est une erreur de syntaxe", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Hard", "concept": "Boucles",
                "text": "Combien de fois la boucle `Pour i := 2 a 5 Faire` va-t-elle s'exécuter ?",
                "explanation": "Elle s'exécute pour i=2, i=3, i=4, et i=5. Cela fait un total de 4 itérations.",
                "choices": [
                    ("4 fois", True),
                    ("5 fois", False),
                    ("3 fois", False),
                    ("Une infinité de fois", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Hard", "concept": "Boucles",
                "text": "Trace d'exécution : `i:=0; TantQue i < 3 Faire i:=i+2; Fin TantQue;`. Que vaut `i` à la fin ?",
                "explanation": "Tour 1: i=0, devient 2. (2<3 est vrai). Tour 2: i=2, devient 4. (4<3 est faux). La boucle s'arrête. i vaut 4.",
                "choices": [
                    ("4", True),
                    ("3", False),
                    ("2", False),
                    ("0", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Hard", "concept": "Conditions",
                "text": "Dans `Si (X > 5) Alors... Sinon Si (X > 10) Alors...`. Que se passe-t-il si X vaut 15 ?",
                "explanation": "X (15) est plus grand que 5, donc la PREMIÈRE condition est Vraie. Son bloc s'exécute, et le code ignore le reste des `Sinon Si`, même si 15 est aussi > 10.",
                "choices": [
                    ("Seul le bloc du premier Si (X > 5) est exécuté", True),
                    ("Seul le bloc du Sinon Si (X > 10) est exécuté", False),
                    ("Les deux blocs sont exécutés l'un après l'autre", False),
                    ("Le code plante", False)
                ]
            },
            {
                "type": "MCQ", "difficulty": "Hard", "concept": "Types",
                "text": "Que produira la ligne : `Ecrire(\"5\" + \"5\");` ?",
                "explanation": "Puisque les 5 sont entre guillemets, ce sont des Chaînes de caractères. Le signe + agit comme une concaténation, collant les textes bout à bout.",
                "choices": [
                    ("55", True),
                    ("10", False),
                    ("Une erreur", False),
                    ("0", False)
                ]
            }
        ]

        # Insert into DB
        for q_data in questions_data:
            q = Question(
                chapter_id=ch1.id,
                type=q_data['type'],
                difficulty=q_data['difficulty'],
                concept=q_data['concept'],
                text=q_data['text'],
                explanation=q_data['explanation']
            )
            db.session.add(q)
            db.session.flush() # to get q.id

            for choice_text, is_correct in q_data['choices']:
                c = Choice(
                    question_id=q.id,
                    text=choice_text,
                    is_correct=is_correct
                )
                db.session.add(c)

        db.session.commit()
        print(f"{len(questions_data)} questions insérées avec succès dans la base de données.")


if __name__ == '__main__':
    seed_chapter_1()
