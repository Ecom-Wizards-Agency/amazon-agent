# Design skills: selective installation

This design package selects two skills from this repository. It is not a Company
AI Skills capability pack or a full Amazon operator installation.

| Skill | Purpose |
| --- | --- |
| `amazon-listing-images` | Concepts, image order and exact copy from product and POE data |
| `amazon-product-photography` | Photo prompts, generation, editing and enhancement |

The canonical sources stay in `skills/` here. A local source checkout does not
activate Seller Central workflows, browser services, schedules or other Amazon
skills. Existing Company AI Skills remain separate; its copywriting skills are
helpful but optional. Figma layout installation is outside this package.

## Copy-ready installation prompt

Paste this into the designer's coding assistant. Use `main` after PR 65 is merged.
For an explicitly requested preview, add: "Use branch feat/amazon-listing-images
for this installation." Never silently switch an existing checkout's branch.

```text
Installiere mir ausschließlich die beiden Design-Skills aus diesem Repository:
https://github.com/Ecom-Wizards-Agency/amazon-agent

- skills/amazon-listing-images
- skills/amazon-product-photography

Nutze main, sofern ich keinen anderen Branch angebe. Verwende vorhandenen
GitHub-Zugriff. Frage nicht nach Tokens oder Passwörtern im Chat.

Prüfe zuerst meine verwendeten AI-Runtimes und vorhandenen Installationen.
Verwende einen passenden vorhandenen Checkout oder klone das Repository in einen
lokalen Quellordner, bevorzugt ~/os/amazon-agent. Auf Windows nutze den passenden
Benutzerpfad. Bewahre lokale Änderungen und bestehende Branches. Aktualisiere
einen sauberen passenden Checkout nur per Fast-forward. Verwende sonst einen
separaten Checkout, ohne bestehende Arbeit umzuschreiben.

Binde nur die zwei genannten Skill-Ordner einschließlich ihrer references/ und
agents/ ein. Nutze die bestehenden Skill-Verzeichnisse der von mir verwendeten
Runtimes: bei Codex das konfigurierte CODEX_HOME/skills, sonst ~/.codex/skills;
bei Claude Code ~/.claude/skills. Erzeuge bevorzugt Verzeichnis-Symlinks auf den
Quell-Checkout, damit spätere Updates dieselbe Quelle verwenden. Nutze vorhandene
Setup-Helfer nur für diese beiden Verknüpfungen, nicht das komplette Bootstrap.

Eine bereits korrekte Verknüpfung bleibt bestehen. Überschreibe oder lösche keine
gleichnamige unabhängige Installation. Falls Symlinks auf Windows nicht möglich
sind, verwende einen unterstützten gezielten Installer mit vollständigen Ordnern
und dokumentiere, dass diese Kopien nach Quell-Updates erneut installiert werden
müssen. Installiere keine zusätzliche Runtime und keine weiteren Skills.

Führe kein vollständiges Amazon-Agent-Onboarding durch, aktiviere nicht die Rolle
amazon-operator und ändere keine globalen Agent-Anweisungen. Richte weder Seller
Central noch Browser-Dienste, Automationen, Figma oder Bildgenerator-Verbindungen
ein. Diese Installation soll noch keine Bilder generieren und keine Credits
verbrauchen.

Prüfe anschließend beide SKILL.md-Dateien, die zugehörigen Referenzen und die
korrekten Installationsziele. Nenne mir Quell-Branch/Commit, installierte Pfade,
eventuelle Kopien statt Symlinks und wie meine Runtime die Skills neu lädt.
Gib mir zum Schluss je einen kurzen Beispielprompt für Konzepte/Texte und
Foto-Prompts. Eine fehlende optionale Verbindung blockiert die Skill-Installation
nicht.
```

## Use after installation

Concepts and copy:

> Nutze $amazon-listing-images mit diesen Produktdaten und POE-Dateien.
> Marketplace: Deutschland. Texte: Englisch. Erstelle Bildkonzepte, Reihenfolge,
> fertige Texte und visuelle Anweisungen.

Photo prompts:

> Nutze $amazon-product-photography mit diesen Produktfotos und Stilreferenzen.
> Erstelle FLORA-Prompts für einen Packshot, eine Anwendungsszene und ein Detailfoto.

Prompt preparation works without FLORA or another image-provider connection.
Generating actual photos requires that provider's authorized access.
