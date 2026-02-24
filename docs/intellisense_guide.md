# IntelliSense User Guide

## Overview
The Algo Compiler now features sophisticated IntelliSense/autocomplete capabilities powered by CodeMirror, providing real-time syntax highlighting and intelligent code suggestions.

## Features

### 1. Syntax Highlighting
All Algo language constructs are color-coded for easy reading:
- **Keywords** (purple): `Algorithme`, `Var`, `Debut`, `Fin`, `Si`, `Pour`, `Tant Que`, etc.
- **Types** (green): `Entier`, `Reel`, `Chaine`, `Booleen`, `Caractere`
- **Built-in Functions** (cyan): `Longueur()`, `Concat()`, `Ecrire()`, `Lire()`
- **Boolean Values** (orange): `Vrai`, `Faux`
- **Operators** (yellow): `Mod`, `Div`, `Et`, `Ou`, `Non`
- **Comments** (gray): `// comment text`
- **Strings** (yellow): `"text"` or `'char'`
- **Numbers** (orange): `123`, `3.14`

### 2. Autocomplete Triggers

#### Manual Trigger
Press **Ctrl+Space** at any time to show autocomplete suggestions.

#### Automatic Trigger
After typing 2 or more characters, autocomplete suggestions appear automatically after a brief delay (300ms).

### 3. Suggestion Types

#### Keywords
Type the beginning of any keyword to see suggestions:
- `Var` → Variable declaration keywords
- `Pour` → Loop keywords
- `Si` → Conditional keywords
- `Ecr` → `Ecrire()` function

#### Variables
The editor automatically tracks variables declared in your `Var` block and suggests them when typing:
- Shows variable name and type
- Prioritized in suggestions when inside `Ecrire()` or `Lire()`

#### Snippets
Type shorthand codes to insert common patterns:
- `pour` → Full `Pour` loop template
- `si` → `Si-Alors-Fin Si` template
- `tantque` → `Tant Que` loop template
- `var` → Variable declaration template
- `ecrire` → `Ecrire()` statement
- `lire` → `Lire()` statement

#### Context-Aware Suggestions
The editor provides different suggestions based on where you're typing:

| Context | Suggestions |
|---------|-------------|
| After `Var` | Type keywords (`Entier`, `Reel`, etc.) |
| After `:` in Var block | Type keywords |
| After `Pour varname` | `de` keyword |
| After `Pour varname de 0` | `a` keyword |
| After `Pour varname de 0 a 10` | `Faire` keyword |
| Inside `Ecrire()` | Declared variables |
| Inside `Lire()` | Declared variables |

### 4. Using Autocomplete

#### Example 1: Writing a Loop
1. Type `pour` → Select the snippet
2. Result: 
   ```
   Pour i de 0 a 10 Faire
       
   Fin Pour;
   ```

#### Example 2: Variable Declaration
1. Type `Var` and press Enter
2. Type variable name, then `:`
3. Autocomplete shows type options: `Entier`, `Reel`, `Chaine`, etc.
4. Select a type and add `;`

#### Example 3: Using Variables
1. After declaring variables in `Var` block
2. Type `Ecr` → Select `Ecrire()`
3. Inside parentheses, start typing a variable name
4. Autocomplete shows matching variables with their types

## Tips

### Keyboard Shortcuts
- **Ctrl+Space**: Show autocomplete
- **Tab**: Insert 4 spaces (proper indentation)
- **Esc**: Close autocomplete menu
- **Enter**: Accept selected suggestion
- **Arrow Keys**: Navigate suggestions

### Best Practices
1. **Use descriptive variable names** - They'll appear in autocomplete
2. **Let autocomplete guide you** - It shows correct syntax
3. **Use snippets for common patterns** - Faster than typing manually
4. **Press Ctrl+Space when stuck** - See available options

### Known Limitations
1. **Reserved Keywords**: Avoid using `a`, `de`, `ou`, `et` as variable names (they're language keywords)
2. **Python Built-ins**: Avoid `len`, `str`, `int`, `list` as variable names (can cause runtime errors)
3. **Case Sensitivity**: Keywords should use proper capitalization (e.g., `Var` not `var`)

## Troubleshooting

### Autocomplete Not Appearing
- Make sure you've typed at least 2 characters
- Try pressing Ctrl+Space manually
- Check browser console for JavaScript errors

### Wrong Suggestions
- The editor may need context - type more characters
- Use Ctrl+Space to see all available options
- Check if you're in the right context (e.g., inside `Var` block)

### Syntax Highlighting Not Working
- Refresh the page
- Check browser console for errors
- Ensure `algo-mode.js` is loaded correctly

## Testing Your IntelliSense

To verify IntelliSense is working:

1. **Open the web interface** at http://localhost:5000
2. **Clear the editor** and start typing:
   ```
   Algorithme Test;
   Var
   ```
3. **Press Ctrl+Space** - You should see type suggestions
4. **Type `x : Ent`** - Autocomplete should suggest `Entier`
5. **Type `Pour`** - Snippet should be available
6. **Check syntax highlighting** - Keywords should be colored

If any of these don't work, check the browser console (F12) for errors.
