import json
import random
import os

GENERIC_WRONG_ANSWERS = [
    "C'est une erreur de compilation.",
    "C'est impossible avec cette structure.",
    "Cela provoque une boucle infinie.",
    "L'ordinateur va planter (Fuite de Mémoire).",
    "Cela retourne toujours la valeur 0.",
    "Il faut utiliser un tableau bidimensionnel à la place.",
    "Cela dépend uniquement du système d'exploitation.",
    "La complexité sera toujours de O(n^2).",
    "Seul un type Booléen est autorisé ici.",
    "Cela nécessite d'importer une bibliothèque externe spéciale.",
    "Le compilateur ignorera cette instruction.",
    "La structure deviendra une constante figée.",
    "Le système le convertira automatiquement en chaîne de caractères.",
    "Cette opération n'existe pas en algorithmique standard.",
    "Cela renverra un nombre aléatoire.",
    "Il faut absolument utiliser une boucle Pour.",
    "C'est une fonctionnalité obsolète.",
    "La taille de la mémoire RAM sera dépassée.",
    "L'index dépassera automatiquement la taille maximale."
]

def pad_choices(choices, correct_text):
    # Ensure choices has exactly 5 incorrect answers
    final_choices = [{"text": correct_text, "is_correct": True}]
    
    incorrects = [c for c in choices if c != correct_text]
    
    # Fill up to 5 incorrect choices
    pool = list(GENERIC_WRONG_ANSWERS)
    random.shuffle(pool)
    
    while len(incorrects) < 5:
        w = pool.pop()
        if w not in incorrects:
            incorrects.append(w)
            
    # Add exactly 5 incorrect
    for w in incorrects[:5]:
        final_choices.append({"text": w, "is_correct": False})
        
    random.shuffle(final_choices) # Shuffle so correct isn't always first
    return final_choices

def build_quiz(topic_data, filename):
    out = []
    
    # If the user didn't provide 20, we can duplicate and mutate slightly or just trust we have 20.
    # We will provide exactly 20 questions in the raw data below.
    for i, q in enumerate(topic_data):
        c_idx = q.get('correct_idx', 0)
        correct_txt = q['choices'][c_idx]
        
        built_q = {
            "type": "MCQ",
            "difficulty": q['difficulty'],
            "concept": q['concept'],
            "text": q['text'],
            "explanation": q['explanation'],
            "choices": pad_choices(q['choices'], correct_txt)
        }
        out.append(built_q)
        
    filepath = os.path.join(r"c:\Users\adel\Documents\Python Codes\PjojectAlgo\Algorithemic_language_compiler\src\web\data\quizzes", filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=4)
    print(f"Created {filename} with {len(out)} questions. (Each has {len(out[0]['choices'])} choices)")

# ======================= DATA =======================

enregistrements_raw = [
    {
        "difficulty": "Easy", "concept": "Définition",
        "text": "Qu'est-ce qu'un enregistrement (Structure) ?",
        "explanation": "Permet de regrouper plusieurs champs de types différents sous une même entité.",
        "choices": [
            "Une structure de données pouvant regrouper des champs de types différents",
            "Un tableau où tous les éléments sont obligatoirement du même type"
        ]
    },
    {
        "difficulty": "Easy", "concept": "Accès",
        "text": "Si `E` est un enregistrement et `Nom` est l'un de ses champs. Comment y accéder ?",
        "explanation": "On utilise l'opérateur point (.).",
        "choices": ["E.Nom", "E[Nom]", "E->Nom", "Nom(E)"]
    },
    {
        "difficulty": "Easy", "concept": "Définition",
        "text": "Un enregistrement peut-il contenir un autre enregistrement ?",
        "explanation": "Oui, c'est l'imbrication d'enregistrements.",
        "choices": ["Oui, c'est tout à fait possible", "Non, seuls les types primitifs sont autorisés"]
    },
    {
        "difficulty": "Medium", "concept": "Déclaration",
        "text": "Lors de la déclaration d'un enregistrement, que faut-il spécifier pour chaque composant ?",
        "explanation": "Chaque champ a besoin d'un identifiant et d'un type.",
        "choices": [
            "L'identifiant du champ et son type",
            "Seulement l'identifiant du champ"
        ]
    },
    {
        "difficulty": "Medium", "concept": "Affectation",
        "text": "Si P1 et P2 sont de même type enregistrement. Que fait `P1 := P2` ?",
        "explanation": "L'affectation globale copie champ par champ P2 dans P1.",
        "choices": [
            "Tous les champs de P2 sont copiés un par un dans P1",
            "On obtient une erreur, il faut affecter champ par champ"
        ]
    },
    {
        "difficulty": "Medium", "concept": "Tableaux",
        "text": "Pour un tableau de 10 enregistrements 'Etudiant'. Comment lire la Note du 5ème ?",
        "explanation": "Tab[5].Note accède d'abord au 5ème élément, puis à son champ.",
        "choices": ["Tab[5].Note", "Tab.Note[5]", "Tab.5.Note"]
    },
    {
        "difficulty": "Hard", "concept": "Comparaison",
        "text": "Peut-on utiliser `Si P1 = P2` pour vérifier l'égalité totale des enregistrements ?",
        "explanation": "En algorithmique classique, cela est interdit. Il faut comparer champ par champ.",
        "choices": [
            "Non, en général il faut comparer chaque champ individuellement",
            "Oui, la machine fait une comparaison de bits automatiques"
        ]
    },
    {
        "difficulty": "Hard", "concept": "Conception",
        "text": "Pour gérer 100 contacts (Nom, Numéro), quelle est la meilleure modélisation ?",
        "explanation": "Un Tableau contenant 100 éléments de type Enregistrement (Contact).",
        "choices": [
            "Un tableau dont les éléments sont des enregistrements",
            "Un enregistrement contenant 100 champs"
        ]
    },
    {
        "difficulty": "Medium", "concept": "Type vs Variable",
        "text": "Différence entre Type Enregistrement et Variable de ce type ?",
        "explanation": "Le Type est le modèle, la variable est l'instanciation en mémoire.",
        "choices": [
            "Le TYPE décrit le modèle, la variable alloue la mémoire",
            "Le TYPE réserve la mémoire, la variable en libère"
        ]
    },
    {
        "difficulty": "Easy", "concept": "Flexibilité",
        "text": "Un enregistrement peut avoir 'Titre' (Chaine) et 'Annee' (Entier) simultanément.",
        "explanation": "Vrai, contrairement au tableau qui est homogène.",
        "choices": ["Vrai", "Faux"]
    },
    # Q11-Q20 added
    {
        "difficulty": "Medium", "concept": "Initialisation",
        "text": "Les champs d'une variable de type pointeur vers un enregistrement après allocation avec `allouer()` contiennent quoi par défaut ?",
        "explanation": "Après allocation, le contenu est indéterminé (ou garbage).",
        "choices": ["Des valeurs indéterminées (ordures mémoires)", "NIL ou NULL pour tous les champs", "La valeur 0 pour les entiers"]
    },
    {
        "difficulty": "Hard", "concept": "Pointeur",
        "text": "Si `P` pointe vers un enregistrement `Contact`, comment accéder au `Nom` ?",
        "explanation": "On déréférence P avec P^ puis on accède au champ.",
        "choices": ["P^.Nom", "P.Nom", "P->Nom", "Nom^.P"]
    },
    {
        "difficulty": "Easy", "concept": "Différence",
        "text": "Quelle est la différence MAJEURE entre un Tableau et un Enregistrement ?",
        "explanation": "Tableau = Homogène (même type), Enregistrement = Hétérogène (types variés).",
        "choices": ["Un tableau est homogène, un enregistrement peut être hétérogène", "L'enregistrement est dynamique, le tableau est statique"]
    },
    {
        "difficulty": "Medium", "concept": "Limites",
        "text": "Combien de champs un enregistrement peut-il contenir ?",
        "explanation": "Logiquement aucune limite stricte, la limitation est fixée par le langage ou la RAM.",
        "choices": ["Théoriquement aucune limite, dépend du compilateur", "Un maximum de 255 champs"]
    },
    {
        "difficulty": "Medium", "concept": "Paramètre",
        "text": "Passer un enregistrement volumineux par VALEUR (Donnée) à une fonction implique quoi ?",
        "explanation": "Une copie complète en mémoire, ce qui est lourd. Préférer passage par variable (Donnée/Résultat).",
        "choices": ["Une copie complète de tous les champs dans la pile", "Juste la copie de son adresse", "Rien, c'est impossible"]
    },
    {
        "difficulty": "Hard", "concept": "Tableau de Pointeurs",
        "text": "Un tableau `Tab` contient des pointeurs vers des Enregistrements. Comment lire le champ `Val` du 3e élément ?",
        "explanation": "On accède au pointeur Tab[3], on le déréférence (Tab[3]^), puis on accède à Val.",
        "choices": ["Tab[3]^.Val", "Tab^[3].Val", "Tab[3].Val^"]
    },
    {
        "difficulty": "Easy", "concept": "Stockage",
        "text": "Comment les champs d'un enregistrement sont-ils stockés en mémoire RAM ?",
        "explanation": "Généralement de façon contiguë (les uns à côté des autres).",
        "choices": ["De façon contiguë (adjacente)", "Éparpillés aléatoirement dans la RAM", "Chaque champ dans un fichier différent"]
    },
    {
        "difficulty": "Easy", "concept": "Taille",
        "text": "Comment calculer la taille en mémoire d'un enregistrement ?",
        "explanation": "C'est grosso modo la somme de la taille de ses champs (avec parfois du padding).",
        "choices": ["La somme de l'encombrement de tous ses champs", "La taille du champ le plus grand multipliée par le nombre de champs"]
    },
    {
        "difficulty": "Hard", "concept": "Structures Récursives",
        "text": "Un enregistrement peut-il avoir un champ qui est un pointeur vers son propre type ?",
        "explanation": "Oui, c'est le principe des listes chaînées et arbres.",
        "choices": ["Oui, c'est la base des structures de données récursives (listes, arbres)", "Non, cela crée un paradoxe infini de compilation"]
    },
    {
        "difficulty": "Medium", "concept": "Lecture",
        "text": "Peut-on faire `Lire(E)` où `E` est un enregistrement entier ?",
        "explanation": "En algo, non. Il faut lire champ par champ (Ex: Lire(E.Nom); Lire(E.Age);).",
        "choices": ["Non, il faut lire (ou afficher) chaque champ individuellement", "Oui, le compilateur demande tous les champs d'un coup"]
    }
]

listes_chainees_raw = [
    {
        "difficulty": "Easy", "concept": "Définition",
        "text": "Qu'est-ce qu'une liste chaînée ?",
        "explanation": "Une séquence d'éléments où chaque nœud pointe vers le suivant.",
        "choices": ["Une structure de données dynamique composée de nœuds liés par pointeurs", "Un tableau de taille fixe"]
    },
    {
        "difficulty": "Easy", "concept": "Nœud",
        "text": "De quoi est composé un 'Nœud' dans une liste chaînée simple ?",
        "explanation": "Une donnée et un pointeur Suivant.",
        "choices": ["Une valeur (donnée) et un pointeur vers le nœud suivant", "Un entier et un booléen"]
    },
    {
        "difficulty": "Easy", "concept": "Allocation",
        "text": "La taille d'une liste chaînée peut varier dynamiquement.",
        "explanation": "Vrai, via pointeurs.",
        "choices": ["Vrai, la mémoire est gérée à l'exécution", "Faux, la taille est fixée à la compilation"]
    },
    {
        "difficulty": "Medium", "concept": "Structure",
        "text": "Que contient le pointeur 'Suivant' du tout DERNIER nœud ?",
        "explanation": "NIL ou NULL.",
        "choices": ["NIL (ou NULL)", "L'adresse du premier nœud"]
    },
    {
        "difficulty": "Medium", "concept": "Tête",
        "text": "Si `Tete` = `NIL`. Que déduit-on ?",
        "explanation": "La liste est vide.",
        "choices": ["La liste est complètement vide", "La liste est pleine"]
    },
    {
        "difficulty": "Medium", "concept": "Insertion",
        "text": "Particularité de l'insertion en Tête (début) ?",
        "explanation": "C'est immédiat, complexité O(1).",
        "choices": ["C'est une opération en temps constant O(1)", "Il faut décaler tous les autres éléments O(n)"]
    },
    {
        "difficulty": "Hard", "concept": "Parcours",
        "text": "Boucle adaptée pour parcourir une liste via pointeur P ?",
        "explanation": "TantQue P <> NIL Faire ...",
        "choices": ["TantQue P <> NIL Faire ... P := P^.Suivant;", "Pour i := 1 à Taille Faire"]
    },
    {
        "difficulty": "Hard", "concept": "Accès",
        "text": "On peut accéder instantanément au 100ème élément.",
        "explanation": "Faux, accès séquentiel O(n).",
        "choices": ["Faux, l'accès est strictement séquentiel", "Vrai, via un index direct"]
    },
    {
        "difficulty": "Hard", "concept": "Libération",
        "text": "Que se passe-t-il si vous perdez le pointeur Tete sans Libérer ?",
        "explanation": "Fuite de mémoire.",
        "choices": ["Une fuite de mémoire (Memory Leak)", "La liste est automatiquement supprimée"]
    },
    {
        "difficulty": "Medium", "concept": "Pointeur",
        "text": "A quoi sert le symbole `^` ?",
        "explanation": "Déréférencer un pointeur.",
        "choices": ["Accéder à la valeur pointée par l'adresse", "Multiplier des pointeurs entre eux"]
    },
    {
        "difficulty": "Medium", "concept": "Insertion Milieu",
        "text": "Insérer un nœud entre A et B nécessite de...",
        "explanation": "Nouv^.Suiv := B, A^.Suiv := Nouv",
        "choices": ["Lier le Nouveau à B, puis A au Nouveau", "Écraser B et mettre le Nouveau"]
    },
    {
        "difficulty": "Hard", "concept": "Suppression Tête",
        "text": "Pour supprimer le premier élément, comment mettre à jour Tete ?",
        "explanation": "Tete := Tete^.Suivant, suivi d'un Liberer sur l'ex-tete.",
        "choices": ["Tete := Tete^.Suivant", "Tete := NIL"]
    },
    {
        "difficulty": "Medium", "concept": "Double Chaînage",
        "text": "Qu'apporte une liste DOUBLEMENT chaînée ?",
        "explanation": "Pouvoir parcourir en arrière grâce au pointeur 'Precedent'.",
        "choices": ["Un pointeur vers le nœud précédent, permettant le parcours arrière", "Elle double la vitesse du processeur"]
    },
    {
        "difficulty": "Medium", "concept": "Recherche",
        "text": "Quelle est la complexité de recherche d'une valeur dans une liste chaînée simple de taille n ?",
        "explanation": "On doit tout parcourir : O(n).",
        "choices": ["O(n) dans le pire des cas", "O(1) car on a des pointeurs"]
    },
    {
        "difficulty": "Medium", "concept": "Liste Circulaire",
        "text": "Dans une liste circulaire simple, vers quoi pointe le dernier élément ?",
        "explanation": "Il pointe vers la Tête.",
        "choices": ["Vers le premier élément de la liste (Tête)", "Vers l'avant-dernier élément"]
    },
    {
        "difficulty": "Easy", "concept": "Tableau vs Liste",
        "text": "Quel est le grand inconvénient d'une liste chaînée face au tableau ?",
        "explanation": "Les pointeurs coûtent de la mémoire mémoire supplémentaire, et l'accès n'est pas indexé.",
        "choices": ["L'absence d'accès direct par index et le coût mémoire des pointeurs", "La liste ne peut stocker que des Entiers"]
    },
    {
        "difficulty": "Hard", "concept": "Suppression Fin",
        "text": "Pour supprimer de la FIN d'une liste chaînée simple (sans queue pointer), il faut :",
        "explanation": "Parcourir jusqu'à l'avant-dernier nœud.",
        "choices": ["Parcourir la liste pour trouver l'avant-dernier nœud et modifier son 'Suivant'", "Aller directement au bout en O(1)"]
    },
    {
        "difficulty": "Hard", "concept": "Opérations Pointeur",
        "text": "Que signifie `P := P^.Suivant^.Suivant` ?",
        "explanation": "Sauter 2 maillons d'un coup.",
        "choices": ["P avance de deux maillons dans la liste", "P recule de deux maillons"]
    },
    {
        "difficulty": "Easy", "concept": "Mémoire",
        "text": "Où sont stockés les maillons d'une liste chaînée pendant l'exécution ?",
        "explanation": "Dans le Tas (Heap).",
        "choices": ["Dans la zone du Tas (Heap dynamique)", "Dans le processeur directement"]
    },
    {
        "difficulty": "Medium", "concept": "Algorithmique",
        "text": "Comment inverser une liste chaînée simple ?",
        "explanation": "Manipuler les pointeurs pour que chaque Suivant pointe sur l'élément précédent.",
        "choices": ["Changer la direction des pointeurs 'Suivant' sans recréer de maillons", "Inverser chaque valeur une par une par swap"]
    }
]

files_raw = [
    {
        "difficulty": "Easy", "concept": "Principe",
        "text": "Principe fondamental d'une File (Queue) ?",
        "explanation": "Premier Arrivé, Premier Servi (FIFO).",
        "choices": ["FIFO (First In, First Out)", "LIFO (Last In, First Out)"]
    },
    {
        "difficulty": "Easy", "concept": "Opérations",
        "text": "L'opération qui ajoute un élément s'appelle ?",
        "explanation": "Enfiler ou Enqueue.",
        "choices": ["Enfiler (Enqueue)", "Dépiler (Pop)"]
    },
    {
        "difficulty": "Easy", "concept": "Opérations",
        "text": "Où s'effectuent ajouts et retraits ?",
        "explanation": "Ajout Queue, Retrait Tête.",
        "choices": ["Ajout à l'Arrière (Queue), Retrait à l'Avant (Tête)", "Tout à l'avant"]
    },
    {
        "difficulty": "Medium", "concept": "Structure",
        "text": "Une File peut être implémentée via un Tableau statique.",
        "explanation": "Vrai, souvent circulaire.",
        "choices": ["Vrai, on gère un index de Tête et un de Queue", "Faux, c'est obligatoirement une liste chaînée"]
    },
    {
        "difficulty": "Medium", "concept": "File Circulaire",
        "text": "Intérêt de la file circulaire en tableau ?",
        "explanation": "Réutiliser les cases du début.",
        "choices": ["Éviter le gaspillage d'espace au début du tableau lors des défilements", "Tri automatique"]
    },
    {
        "difficulty": "Easy", "concept": "État",
        "text": "Il faut vérifier si la file est vide avant de Défiler.",
        "explanation": "Vrai, pour ne pas défiler le vide.",
        "choices": ["Vrai", "Faux"]
    },
    {
        "difficulty": "Hard", "concept": "Exercice",
        "text": "F vide. Enfiler(1); Enfiler(2); Défiler(); Enfiler(3). Que reste-il ?",
        "explanation": "1 sort. 2 et 3 restent.",
        "choices": ["[2, 3]", "[1, 3]", "[3, 2]"]
    },
    {
        "difficulty": "Medium", "concept": "Applications",
        "text": "Où utilise-t-on une File en informatique ?",
        "explanation": "File d'attente d'impression (Spooler).",
        "choices": ["La gestion des travaux d'impression envoyés vers une imprimante", "La fonction Ctrl+Z"]
    },
    {
        "difficulty": "Hard", "concept": "Implémentation Liste",
        "text": "Si `Queue` et `Tete` pointent sur le même maillon ?",
        "explanation": "La file a 1 élément.",
        "choices": ["La file contient exactement 1 seul élément", "Elle est vide"]
    },
    {
        "difficulty": "Easy", "concept": "Synthèse",
        "text": "Mot-clé pour File ?",
        "explanation": "FIFO.",
        "choices": ["FIFO", "LIFO", "FILO"]
    },
    {
        "difficulty": "Medium", "concept": "Erreur",
        "text": "Qu'est-ce que l'OverFlow dans une file ?",
        "explanation": "Quand on essaie d'Enfiler mais que le support de stockage est vide ou dépassé.",
        "choices": ["Tenter d'enfiler dans une file basée sur tableau qui est déjà pleine", "Tenter de défiler une file vide"]
    },
    {
        "difficulty": "Medium", "concept": "Erreur",
        "text": "Qu'est-ce que l'UnderFlow dans une file ?",
        "explanation": "Quand on essaie de retirer de rien.",
        "choices": ["Tenter de défiler (retirer) alors que la file est vide", "Tenter d'enfiler un fichier trop lourd"]
    },
    {
        "difficulty": "Hard", "concept": "Calcul de taille",
        "text": "Dans une file circulaire tableau avec Tete (T) et Queue (Q) et Capacite MAX. Comment trouver le nombre d'éléments ?",
        "explanation": "Modulo math: (Q - T + MAX) % MAX.",
        "choices": ["(Queue - Tête + Max) Modulo Max", "Queue moins Tête, toujours"]
    },
    {
        "difficulty": "Medium", "concept": "Priorité",
        "text": "Qu'est-ce qu'une File de Priorité ?",
        "explanation": "Une file où l'élément sorti est celui avec le plus haut degré d'importance, pas le plus vieux.",
        "choices": ["Une file où le retrait se fait selon un score/priorité et non l'ordre d'arrivée", "Une file uniquement réservée aux administrateurs"]
    },
    {
        "difficulty": "Medium", "concept": "Opérations Pointeur",
        "text": "Dans une file implémentée en liste chaînée, complexité de Enfiler et Défiler si l'on a les pointeurs Tete et Queue ?",
        "explanation": "O(1) pour les deux !",
        "choices": ["O(1) pour l'enfilement et O(1) pour le défilement", "O(n) et O(n)"]
    },
    {
        "difficulty": "Hard", "concept": "Structure à Deux Piles",
        "text": "Peut-on simuler le comportement d'une File en utilisant uniquement DEUX Piles ?",
        "explanation": "Oui, en empilant sur P1, et pour défiler, on renverse tout dans P2.",
        "choices": ["Oui, c'est l'algorithme classique d'implémentation d'une file avec 2 piles", "Non, les mathématiques prouvent que c'est impossible"]
    },
    {
        "difficulty": "Medium", "concept": "Arbres",
        "text": "Lors d'un parcours 'En Largeur' (BFS) d'un arbre binaire, quelle structure est indispensable ?",
        "explanation": "La file d'attente.",
        "choices": ["Une File (Queue)", "Une Pile (Stack)"]
    },
    {
        "difficulty": "Easy", "concept": "Comparaison",
        "text": "A la caisse d'un supermarché, la structure de données humaine formée est :",
        "explanation": "Une file.",
        "choices": ["Une file d'attente FIFO", "Une pile d'assiettes LIFO"]
    },
    {
        "difficulty": "Medium", "concept": "Vérification",
        "text": "Dans une File tableau basique non circulaire, quand la Queue atteint MAX, la file est considérée Pleine...",
        "explanation": "Même si on a défilé des éléments au début. D'où la nécessité de la rendre circulaire.",
        "choices": ["Même s'il y a des cases vides créées à l'avant par des défilements antérieurs", "Il n'y a pas de problème, on repousse tout au début gratuitement"]
    },
    {
        "difficulty": "Hard", "concept": "Cas extrême",
        "text": "Dans une file circulaire, comment distinguer File Pleine et File Vide ?",
        "explanation": "Une méthode est de garder une variable 'NbElements' ou laisser une case vide intentionnelle.",
        "choices": ["Utiliser un compteur d'éléments ou sacrifier une case du tableau comme marge", "Vérifier si Tête vaut -1"]
    }
]

piles_raw = [
    {
        "difficulty": "Easy", "concept": "Principe",
        "text": "Principe de fonctionnement de la Pile (Stack) ?",
        "explanation": "Dernier arrivé, premier sorti.",
        "choices": ["LIFO (Last In, First Out)", "FIFO"]
    },
    {
        "difficulty": "Easy", "concept": "Opérations",
        "text": "Opération pour ajouter ?",
        "explanation": "Empiler.",
        "choices": ["Empiler (Push)", "Enfiler"]
    },
    {
        "difficulty": "Easy", "concept": "Opérations",
        "text": "Où empile et dépile-t-on ?",
        "explanation": "Toujours au Sommet.",
        "choices": ["Exclusivement au Sommet (Top) de la pile", "A la base"]
    },
    {
        "difficulty": "Medium", "concept": "Applications",
        "text": "Application réelle d'une pile ?",
        "explanation": "Ctrl+Z (Undo).",
        "choices": ["La fonction Annuler (Ctrl+Z)", "Spooler d'impression"]
    },
    {
        "difficulty": "Hard", "concept": "Pratique",
        "text": "Pile vide. Empile 10, 20. Dépile X. Valeur X et Sommet ?",
        "explanation": "X=20, Sommet=10.",
        "choices": ["X = 20, Sommet = 10", "X = 10, Sommet = 20"]
    },
    {
        "difficulty": "Easy", "concept": "État",
        "text": "Vérifier File non Pleine avant Empiler (sur tableau) ?",
        "explanation": "Vrai, sinon Stack Overflow.",
        "choices": ["Vrai", "Faux"]
    },
    {
        "difficulty": "Medium", "concept": "Processeur",
        "text": "Que fait le pointeur d'instruction avec les appels fonctions ?",
        "explanation": "Il empile les adresses de retour (Call stack).",
        "choices": ["La pile d'appels mémoires (Call Stack)", "La file d'attente d'IRQ"]
    },
    {
        "difficulty": "Medium", "concept": "Manipulation",
        "text": "Accès au fond d'une pile sans perdre l'ordre final ?",
        "explanation": "On a besoin d'une pile intermédiaire.",
        "choices": ["Il faut inévitablement déverser dans une seconde pile temporaire", "On lit index 0 instantanément"]
    },
    {
        "difficulty": "Hard", "concept": "Evaluation math",
        "text": "Expression post-fixée avec pile ?",
        "explanation": "Empilant opérandes, lors d'un opérateur on dépile et calcule.",
        "choices": ["Empiler nombres, dépiler lors d'un opérateur, empiler résultat", "Ignorer cette approche"]
    },
    {
        "difficulty": "Easy", "concept": "Synthèse",
        "text": "Cas de l'assiette rangée ?",
        "explanation": "Pile.",
        "choices": ["Une Pile", "Une File"]
    },
    {
        "difficulty": "Hard", "concept": "Parcours Graphe",
        "text": "Lors d'un parcours 'En Profondeur' (DFS), la structure idéale est...",
        "explanation": "La pile. On empile les voisins à explorer en descendant.",
        "choices": ["Une Pile (Stack, souvent implicite via récursivité)", "La File circulaire asynchrone"]
    },
    {
        "difficulty": "Medium", "concept": "Erreur Célèbre",
        "text": "Que signifie Stack Overflow dans le monde de la programmation ?",
        "explanation": "Dépassement de la capacité de la pile (souvent dû à une récursivité infinie).",
        "choices": ["Un dépassement de la mémoire allouée à la pile d'exécution du programme", "Une pile d'assiettes ayant atteint virtuellement le plafond"]
    },
    {
        "difficulty": "Hard", "concept": "Implémentation",
        "text": "Dans une implémentation Liste Chaînée d'une Pile, où fait-on pointer 'Sommet' ?",
        "explanation": "Sur la Tête de la liste chaînée (pour garder O(1)).",
        "choices": ["Vers le premier élément de la liste (La Tête)", "Vers l'avant-dernier maillon"]
    },
    {
        "difficulty": "Medium", "concept": "Conversion",
        "text": "La pile est essentielle pour évaluer ou convertir quelle notation mathématique bien connue ?",
        "explanation": "La Notation Polonaise Inverse (NPI / Postfixée).",
        "choices": ["La Notation Polonaise Inverse (RPN / Postfixée)", "Les équations différentielles de second degré"]
    },
    {
        "difficulty": "Medium", "concept": "Balises HTML",
        "text": "Comment un parseur vérifie-t-il que des balises (HTML ou parenthèses) sont bien équilibrées ?",
        "explanation": "En empilant la balise ouvrante, et en la dépilant lors d'une balise fermante.",
        "choices": ["En ouvrant une balise on empile, en la fermant on dépile et on compare", "Il génère un tableau aléatoire"]
    },
    {
        "difficulty": "Easy", "concept": "Variables locales",
        "text": "Où sont stockées temporairement la majorité des variables locales de fonctions en C ou Algo ?",
        "explanation": "Sur la pile (Call Stack).",
        "choices": ["Dans la zone mémoire appelée la Pile (Stack segment)", "Sur un registre périphérique USB"]
    },
    {
        "difficulty": "Hard", "concept": "Exercice",
        "text": "P = Vide. Empile(A). Empile(B). Empile(C). Depile(X). Que vaut Sommet ?",
        "explanation": "C est dépilé. Le sommet est B.",
        "choices": ["L'élément 'B'", "L'élément 'C'", "L'élément 'A'"]
    },
    {
        "difficulty": "Medium", "concept": "Avantage",
        "text": "Lequel est un AVANTAGE de la pile implémentée en Tableau statique vs Liste chaînée ?",
        "explanation": "Pas de pointeurs, accès direct mémoire.",
        "choices": ["Économie de mémoire (pas de pointeurs) et vitesse pure", "Taille extensible à l'infini"]
    },
    {
        "difficulty": "Hard", "concept": "Palindrome",
        "text": "Comment utiliser utilement une pile pour vérifier si un mot est un Palindrome ?",
        "explanation": "Empiler la première moitié, et dépiler pour comparer avec la deuxième.",
        "choices": ["On empile la 1ère moitié des lettres, puis on dépile en comparant avec la 2ème", "On empile tout et on fait la somme ASCII"]
    },
    {
        "difficulty": "Medium", "concept": "Lecture",
        "text": "Quelle fonction système permet d'observer l'élément au sommet de la pile SANS le retirer ?",
        "explanation": "C'est souvent appelé Peek(Pile).",
        "choices": ["La fonction 'Sommet_Lien(P)' ou 'Peek(P)'", "Il n'y a pas d'autre choix que Pop(P)"]
    }
]

if __name__ == "__main__":
    build_quiz(enregistrements_raw, "enregistrements.json")
    build_quiz(listes_chainees_raw, "listes_chainees.json")
    build_quiz(files_raw, "files.json")
    build_quiz(piles_raw, "piles.json")
