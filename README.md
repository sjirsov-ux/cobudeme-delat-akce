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

## Jedinečné obrázky akcí

Workflow vytváří pro každou akci vlastní fotorealistický ilustrační obrázek podle názvu a popisu. Soubory se ukládají pod ID akce do `assets/event-images/`; při dalších aktualizacích se znovu používají a obrázek jiné akce se nepřiřadí. Nová akce dostane nový obrázek při příštím denním běhu workflow. Selhané generování se zkusí znovu při dalším běhu.

Pro aktivaci přidejte v GitHubu do **Settings → Secrets and variables → Actions** repository secret s názvem `OPENAI_API_KEY`, poté spusťte workflow **Aktualizace veřejného přehledu akcí** ručně. Klíč patří pouze do GitHub Secret, nikdy do aplikace. Generování používá OpenAI Images API a účtuje se zvlášť podle použitého modelu a počtu obrázků; 69 současných akcí znamená 69 prvních generování. Bez nastaveného klíče se feed dál obnovuje, ale nové obrázky se přeskočí.
