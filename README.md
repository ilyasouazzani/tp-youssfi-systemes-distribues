# Projet Systèmes Distribués

## Backend de démonstration
Les services utilisent des données fictives en mémoire. La Gateway route les requêtes vers les services découverts via Eureka. EBank utilise OpenFeign pour récupérer les clients. Le circuit breaker Resilience4j renvoie le compte avec customerAvailable=false si le service clients ne répond pas.

Compiler avec JDK 17 et Maven : mvn -B clean package. Lancer chaque JAR dans un terminal séparé dans l’ordre discovery, customer-service, ebank-service, gateway.

| Vérification | URL |
|---|---|
| Eureka | http://127.0.0.1:8761 |
| Clients par la Gateway | http://127.0.0.1:8080/customers |
| Compte enrichi par Feign | http://127.0.0.1:8080/accounts/ACC-001 |
| Swagger clients | http://127.0.0.1:8081/swagger-ui/index.html |
| Swagger comptes | http://127.0.0.1:8082/swagger-ui/index.html |

Comparer la réponse EBank avant et après l’arrêt de Customer-Service. Vérifier le compte inconnu et le code HTTP 404. Le cas dégradé doit conserver les données du compte et signaler l’absence du client.

## Scénario de vérification

Avec les quatre services démarrés, lancer `pwsh -File verifier-api.ps1`. Pour observer le mode dégradé, arrêter Customer-Service et appeler à nouveau la route des comptes. Après redémarrage, vérifier que le client est retrouvé.

## Agent Spring AI et MCP

Le modèle reçoit la question depuis le chatbot REST. Quand il choisit un outil, le client MCP Streamable HTTP du chatbot appelle le serveur Bank MCP. Ce dernier appelle la Gateway et renvoie les données fictives au modèle avant la réponse finale. Les trois outils sont en lecture seule : list_customers, find_customer et find_account.

    REST / Telegram / Discord
                |
      bank-assistant :8085
                |
         MCP Streamable HTTP
                |
          bank-mcp :8084
                |
           Gateway :8080
             /        \
       Customer      EBank
           ^           |
           +--- Feign -+

Après avoir compilé avec Maven, démarrer les quatre services de la partie 1, puis bank-mcp et bank-assistant dans deux terminaux. Les ports de démonstration écoutent sur 127.0.0.1. Pour démarrer l’assistant, définir OPENAI_API_KEY dans le terminal avec une clé autorisée, puis lancer le JAR. BANK_MODEL et BANK_MODEL_BASE_URL permettent de sélectionner un modèle et un serveur compatibles avec l’API OpenAI et les appels d’outils.

    java -jar bank-mcp/target/bank-mcp-1.0.0.jar
    java -jar bank-assistant/target/bank-assistant-1.0.0.jar

Importer Youssfi.postman_collection.json dans Postman. Les deux routes /api/mcp/** utilisent le client MCP indépendamment de la génération. La route POST /api/chat reçoit un objet question et renvoie un objet answer. Exemple : « Quel est le solde du compte ACC-001 ? ».

## Telegram et Discord

Telegram : définir TELEGRAM_BOT_TOKEN et TELEGRAM_ALLOWED_CHAT_ID, puis lancer python clients/telegram_bot.py. Dans le chat de test autorisé, envoyer /bank Quel est le solde du compte ACC-001 ?

Discord : installer les dépendances de clients/requirements.txt. Dans l’application Discord du bot, activer Message Content Intent et donner au bot accès au canal de test. Définir DISCORD_BOT_TOKEN et DISCORD_ALLOWED_CHANNEL_ID, puis lancer python clients/discord_bot.py. Envoyer !bank Quel est le solde du compte ACC-001 ?

Utiliser uniquement des comptes et des espaces de test autorisés. Les jetons sont lus en variables d’environnement. Aucun jeton n’est nécessaire pour les tests locaux simulant le modèle.

## Tests locaux

Après mvn package, arrêter tout service qui occupe les ports 8080, 8081, 8082, 8084, 8085 ou 8761, puis lancer python tests/integration.py. Le test démarre les agents et services locaux, vérifie les routes HTTP et Swagger UI, liste et appelle les outils via le vrai protocole MCP, puis fait jouer à un serveur local le rôle du modèle OpenAI pour tester un appel d’outil complet. Enfin, il vérifie le fonctionnement dégradé quand Customer-Service s’arrête.

Les essais avec un vrai modèle et les plateformes Telegram et Discord demandent leurs identifiants de test. La collection Postman est fournie et les mêmes routes sont couvertes par le test HTTP automatisé.

Documentation : https://spring.io/projects/spring-cloud/ et https://docs.spring.io/spring-ai/reference/1.1/api/mcp/mcp-client-boot-starter-docs.html

Vérification locale sur Windows et JDK 17 : compilation Maven, routes de la Gateway, OpenAPI et Swagger UI, appel MCP du compte ACC-001, chatbot REST avec modèle simulé, rejet des questions vides et mode dégradé après arrêt de Customer-Service.
