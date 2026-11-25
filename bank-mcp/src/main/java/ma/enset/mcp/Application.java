package ma.enset.mcp;

import org.springframework.ai.support.ToolCallbacks;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.HttpClientErrorException;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }

    @Bean
    ToolCallbackProvider bankToolCallbacks(
            @Value("${bank.gateway-url}") String gateway,
            RestClient.Builder builder) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(1500);
        factory.setReadTimeout(4500);
        var rest = builder.baseUrl(gateway).requestFactory(factory).build();
        return ToolCallbackProvider.from(ToolCallbacks.from(new BankTools(rest)));
    }

    static class BankTools {
        private final RestClient rest;

        BankTools(RestClient rest) { this.rest = rest; }

        @Tool(name = "list_customers", description = "Liste les clients fictifs de la banque de démonstration.")
        public String listCustomers() { return get("/customers"); }

        @Tool(name = "find_customer", description = "Consulte un client fictif par son identifiant numérique.")
        public String findCustomer(@ToolParam(description = "Identifiant du client") long id) {
            if (id < 1) return "{\"error\":\"Identifiant invalide\"}";
            return get("/customers/{id}", id);
        }

        @Tool(name = "find_account", description = "Consulte un compte fictif, par exemple ACC-001.")
        public String findAccount(@ToolParam(description = "Identifiant de compte, format ACC-001") String id) {
            if (id == null || !id.matches("ACC-[0-9]{3}")) return "{\"error\":\"Format de compte invalide\"}";
            return get("/accounts/{id}", id);
        }

        private String get(String uri, Object... args) {
            try {
                return rest.get().uri(uri, args).retrieve().body(String.class);
            } catch (HttpClientErrorException.NotFound ex) {
                return "{\"error\":\"Ressource introuvable\"}";
            } catch (RestClientException ex) {
                return "{\"error\":\"Service temporairement indisponible\"}";
            }
        }
    }
}
