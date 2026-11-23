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

## Étapes restantes
La partie agent Spring AI, le transport MCP, les clients Telegram et Discord et la démo ne sont pas implémentés dans cette version.

Source : https://spring.io/projects/spring-cloud/



## Scénario de vérification

Avec les quatre services démarrés, lancer `pwsh -File verifier-api.ps1`. Pour observer le mode dégradé, arrêter Customer-Service et appeler à nouveau la route des comptes. Après redémarrage, vérifier que le client est retrouvé.
