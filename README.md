# Přehled akcí pro CO BUDEME DĚLAT?

Veřejný datový feed pro obrazovku **Akce tento týden** v aplikaci. Obsah se obnovuje každý den pomocí GitHub Actions a je dostupný jako JSON na:

https://raw.githubusercontent.com/sjirsov-ux/cobudeme-delat-akce/main/events.json

## Zdroje

- Visit Teplice – veřejný kalendář událostí v Teplicích: https://visitteplice.com/aktuality/
- Kam v Ústí – veřejný kalendář událostí v Ústí nad Labem: https://kamvusti.cz/

Kalendáře mohou odkazovat na pořadatele včetně veřejných stránek událostí na Facebooku a Instagramu. Příspěvky z osobních nebo neveřejných profilů sociálních sítí se nestahují. Každá karta odkazuje na zdrojový detail pořadatele, pokud ho veřejný kalendář uvádí.

## Automatická aktualizace

Workflow `.github/workflows/scrape.yml` běží jednou denně v 04:17 UTC a lze jej spustit také ručně v záložce **Actions**. Skript `scripts/scrape_events.py` čte veřejné stránky a ukládá jen události s rozpoznaným budoucím datem. Pokud zdroje selžou nebo nepřinesou žádné termíny, ponechá poslední platný feed.

Poté workflow spustí `scripts/generate_event_images.py`. Existující obrázek k danému ID ponechá. Pro novou akci bez obrázku vytvoří tematický JPEG, uloží jej do `assets/event-images/` a přidá jeho URL do `events.json`. Obrázky porovnává podle SHA-256 proti ostatním uloženým obrázkům; při přesné duplicitě zkusí vytvořit jinou kompozici. Obrázky a feed se publikují společně, takže aplikace dostane stabilní veřejnou URL.

Workflow potřebuje GitHub Actions Secret `OPENAI_API_KEY`. Bez něj generovací skript bezpečně přeskočí volání API; akce se přesto aktualizují a aplikace zobrazí dostupný lokální tematický obrázek nebo neutrální stav bez fotky. OpenAI Images API je placené; vytvoření nových obrázků může účtovat poplatky. Klíč se ukládá pouze do GitHub Secrets a nikdy do mobilní aplikace.

Události používají pole `id`, `title`, `category`, `venue`, `city`, `dateStart`, volitelně `dateEnd`, `imageUrl`, `ticketUrl`, povinné `sourceUrl` a volitelný `description`.

Časy jsou uváděny v časové zóně Europe/Prague. Feed obsahuje jen veřejně dostupné informace a nevyžaduje Firebase ani přístupové klíče.
