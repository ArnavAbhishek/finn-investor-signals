**To:** assessment@enam.com  
**Subject:** IIT Delhi – AI Engineer - 2027

Dear ENAM Team,

Please find my submission for the FINN AI Engineer Build Challenge.

**Working prototype:** [INSERT VERIFIED PUBLIC RENDER URL]  
**GitHub repository:** [INSERT YOUR REPOSITORY URL]  
**AI-assisted build history:** [INSERT ACTUAL CHATGPT/CODING-AGENT SHARE LINKS OR EXPORTS]

I built FINN as a mobile-first investment intelligence workspace around the two workflows in the brief. On the **Push** side, it brings portfolio-specific exchange disclosures into a prioritised feed and offers configurable end-of-day price and volume triggers, with source links and an investor-selectable time window. On the **Pull** side, it examines primary company documents rather than secondary commentary. The research area includes eight analytical lenses and a reproducible, source-linked Infosys case comparing four reported quarters, financial metrics, and management commentary against disclosed results and guidance.

My main product decision was to minimise noise on the opening screen, while letting the investor inspect the original filing and move directly from a signal to deeper company research. I used deterministic rules for thresholds and numerical comparisons; AI-assisted analysis is restricted to retrieved primary documents and is optional. The work is deliberately transparent about unavailable figures and accounting differences—for example, reported operating profit is not presented as EBITDA without evidence.

The main trade-off is public data-source reliability: unofficial NSE website access and Yahoo historical feeds may be unavailable from free cloud hosting, so the interface reports source limitations rather than displaying invented live values. The prototype does not include a licensed exchange feed, fully automated universal quarterly-filing extraction, a complete executive-biography enrichment workflow or 24/7 background notifications. Given more time, I would prioritise a durable issuer-document ingestion pipeline and a verified management-guidance-versus-outcome engine.

The repository includes installation/deployment instructions, test coverage, a source audit, and a requirements-to-feature map. I have included the actual AI-assisted development history as requested.

Thank you for reviewing my submission.

Best regards,  
[YOUR NAME]  
IIT Delhi
