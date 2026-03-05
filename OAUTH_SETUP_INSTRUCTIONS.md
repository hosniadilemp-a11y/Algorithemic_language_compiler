Les clés API OAuth (Google et GitHub) nécessitent que vous configuriez des applications développeurs sur leurs plateformes respectives. Voici les instructions étape par étape pour les obtenir :

---

### Configuration Google OAuth 2.0

1. Allez sur la [Console Google Cloud](https://console.cloud.google.com/).
2. Créez un nouveau projet (ex: "AlgoCompiler-Auth").
3. Allez dans **API et Services** > **Écran de consentement OAuth**.
   - Type d'utilisateur: **Externe** (ou Interne si GSuite).
   - Remplissez les informations de base (Nom de l'application, e-mail de support).
   - Dans 'Domaines autorisés', ajoutez vos domaines (laissez vide en développement local).
4. Allez dans **API et Services** > **Identifiants**.
   - Cliquez sur **+ CRÉER DES IDENTIFIANTS** > **ID client OAuth**.
   - Type d'application: **Application Web**.
   - Nom: "AlgoCompiler Web".
   - **Origines JavaScript autorisées** : 
     - `http://localhost:5000`
     - `https://algorithemic-language-compiler.onrender.com`
   - **URI de redirection autorisés** :
     - `http://localhost:5000/auth/google`
     - `https://algorithemic-language-compiler.onrender.com/auth/google`
5. Copiez le **Client ID** et le **Client Secret**.
6. Définissez-les comme variables d'environnement dans votre terminal (local) ou dans le dashboard **Render** (Environment) :
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`

---

### Configuration GitHub OAuth

1. Allez sur GitHub, cliquez sur votre photo de profil en haut à droite > **Settings**.
2. Dans le menu de gauche (tout en bas), cliquez sur **Developer settings**.
3. Cliquez sur **OAuth Apps** > **New OAuth App**.
4. Remplissez le formulaire :
   - **Application name**: AlgoCompiler
   - **Homepage URL**: `https://algorithemic-language-compiler.onrender.com`
   - **Authorization callback URL**: `https://algorithemic-language-compiler.onrender.com/auth/github`
5. Cliquez sur **Register application**.
6. Sur la page suivante, vous verrez votre **Client ID**. Copiez-le.
7. Cliquez sur **Generate a new client secret** et copiez le texte généré.
8. Définissez-les comme variables d'environnement dans **Render** :
   - `GITHUB_CLIENT_ID`
   - `GITHUB_CLIENT_SECRET`

---

### Configuration Email (SMTP)

Pour l'envoi d'emails de vérification, vous pouvez utiliser un compte Gmail gratuit ou un service comme SendGrid.

**Méthode Gmail :**
1. Allez dans les paramètres de sécurité de votre compte Google.
2. Activez l'Authentification à deux facteurs.
3. Recherchez "Mots de passe d'application" (App passwords) et créez-en un pour "Messagerie".
4. Utilisez le mot de passe de 16 caractères généré pour la variable `MAIL_PASSWORD`.

**Variables d'environnement SMTP :**
- `export MAIL_SERVER="smtp.gmail.com"`
- `export MAIL_PORT="587"`
- `export MAIL_USE_TLS="true"`
- `export MAIL_USERNAME="votre_email@gmail.com"`
- `export MAIL_PASSWORD="mot_de_passe_application_16_lettres"`
- `export MAIL_DEFAULT_SENDER="AlgoCompiler <votre_email@gmail.com>"`

---
**Note sur la sécurité :** En production, utilisez de vraies variables d'environnement et ne codez jamais ces clés en dur dans `app.py`.
