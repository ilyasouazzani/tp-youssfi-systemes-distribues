package ma.enset.assistant;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import io.modelcontextprotocol.client.McpSyncClient;
import io.modelcontextprotocol.spec.McpSchema.CallToolRequest;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.tool.ToolCallback;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@SpringBootApplication
public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}

@RestController
@RequestMapping("/api")
class ChatController {
    private final ChatClient chat;
    private final McpSyncClient bank;

    ChatController(ChatClient.Builder builder, List<ToolCallbackProvider> providers,
                   List<McpSyncClient> clients) {
        ToolCallback[] tools = providers.stream()
            .flatMap(provider -> Arrays.stream(provider.getToolCallbacks()))
            .toArray(ToolCallback[]::new);
        this.chat = builder.defaultSystem("""
            Tu es l’assistant d’une banque fictive. Réponds en français.
            Pour tout fait sur un client, un compte ou un solde, utilise les outils MCP.
            Signale les données introuvables et les services indisponibles.
            N’invente ni identifiant, ni solde. Tu as uniquement accès à des données de démonstration.
            """).defaultToolCallbacks(tools).build();
        this.bank = clients.get(0);
    }

    @PostMapping("/chat")
    Map<String, String> chat(@RequestBody Question input) {
        if (input.question() == null || input.question().isBlank() || input.question().length() > 1000) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Question requise, 1 à 1000 caractères.");
        }
        try {
            String answer = chat.prompt().user(input.question().strip()).call().content();
            if (answer == null || answer.isBlank()) {
                throw new IllegalStateException("Réponse vide");
            }
            return Map.of("answer", answer);
        } catch (RuntimeException error) {
            throw new ResponseStatusException(HttpStatus.BAD_GATEWAY, "Le modèle n’a pas répondu.");
        }
    }

    @GetMapping("/mcp/tools")
    Object tools() { return bank.listTools().tools(); }

    @GetMapping("/mcp/accounts/{id}")
    Object account(@PathVariable String id) {
        if (!id.matches("ACC-[0-9]{3}")) throw new ResponseStatusException(HttpStatus.BAD_REQUEST);
        return bank.callTool(new CallToolRequest("find_account", Map.of("id", id)));
    }

    record Question(String question) {}
}
