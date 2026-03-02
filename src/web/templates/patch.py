with open('/media/hp/Data/Lab-ISI/HOSNI/AlgoCompiler/src/web/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

target = """                <a href="/course" class="btn secondary highlight" title="Ouvrir le cours d'algorithmique">
                    <i class="fas fa-graduation-cap"></i> Cours
                </a>
                <div class="separator"></div>
                <a href="/problems" class="btn secondary highlight" title="Défis de codage">
                    <i class="fas fa-laptop-code"></i> Défis
                
                    <i class="fas fa-graduation-cap"></i> Cours
                </a>
                <div class="separator"></div>"""

replace = """                <a href="/course" class="btn secondary highlight" title="Ouvrir le cours d'algorithmique">
                    <i class="fas fa-graduation-cap"></i> Cours
                </a>
                <div class="separator"></div>
                <a href="/problems" class="btn secondary highlight" title="Défis de codage">
                    <i class="fas fa-laptop-code"></i> Défis
                </a>
                <div class="separator"></div>"""

if target in content:
    content = content.replace(target, replace)
    with open('/media/hp/Data/Lab-ISI/HOSNI/AlgoCompiler/src/web/templates/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched successfully")
else:
    print("Target not found")
