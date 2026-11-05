# Přehled akcí pro CO BUDEME DĚLAT?

Veřejný datový feed pro obrazovku **Akce tento týden** v aplikaci. Obsah se obnovuje každý den pomocí GitHub Actions a je dostupný jako JSON na:

https://raw.githubusercontent.com/sjirsov-ux/cobudeme-delat-akce/main/events.json

## Zdroje

- Visit Teplice – veřejný kalendář událostí v Teplicích: https://visitteplice.com/aktuality/
- Kam v Ústí – veřejný kalendář událostí v Ústí nad Labem: https://kamvusti.cz/
- Kalendáře mohou odkazovat na pořadatele včetně veřejných stránek událostí na Facebooku a Instagramu.

Příspěvky z osobních nebo neveřejných profilů sociálních sítí se nestahují. Každá karta odkazuje na zdrojový detail pořadatele, pokud ho veřejný kalendář uvádí.

## Automatická aktualizace

Workflow `.github/workflows/scrape.yml` běží jednou denně v 04:17 UTC a lze jej spustit také ručně v záložce **Actions**. Skript `scripts/scrape_events.py` čte veřejné stránky a ukládá jen události s rozpoznaným budoucím datem. Pokud zdroje selžou nebo nepřinesou žádné termíny, ponechá poslední platný feed.

Události používají pole `id`, `title`, `category`, `venue`, `city`, `dateStart`, volitelně `dateEnd`, `imageUrl`, `ticketUrl`, povinné `sourceUrl` a volitelný `description`.

Časy jsou uváděny v časové zóně Europe/Prague. Feed obsahuje jen veřejně dostupné informace a nevyžaduje Firebase ani přístupové klíče.

## Připravené generování jedinečných obrázků

Skript `scripts/generate_event_images.py` vytvoří pro každou akci tematický obrázek a uloží jej pod ID akce do `assets/event-images/`. Zapsaná URL je jedinečná pro danou akci; již uložený soubor se při dalších aktualizacích znovu nepoužije pro jinou akci. Skript je připravený, ale zatím není zapojený do denního workflow.

Generování používá placené OpenAI Images API. Zapojení do automatického workflow vyžaduje repository secret `OPENAI_API_KEY` v GitHubu a souhlas s úhradou první dávky pro 69 akcí i dalších nových akcí. Klíč se ukládá jen do GitHub Secrets, nikdy do mobilní aplikace.
