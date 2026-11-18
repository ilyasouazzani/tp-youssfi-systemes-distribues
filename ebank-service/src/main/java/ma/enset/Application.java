package ma.enset;
import java.math.BigDecimal;
import java.util.Map;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.cloud.client.circuitbreaker.CircuitBreakerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@EnableFeignClients
@SpringBootApplication
public class Application {
    public static void main(String[] args) { SpringApplication.run(Application.class, args); }
}
@FeignClient(name = "customer-service")
interface Customers {
    @GetMapping("/customers/{id}")
    Customer find(@PathVariable("id") long id);
}
record Customer(long id, String name) {}
record Account(String id, long customerId, BigDecimal balance) {}
record AccountView(Account account, Customer customer, boolean customerAvailable) {}
@RestController
@RequestMapping("/accounts")
class AccountController {
    private final Map<String, Account> accounts =
        Map.of("ACC-001", new Account("ACC-001", 1, new BigDecimal("1200.00")));
    private final Customers customers;
    private final CircuitBreakerFactory<?, ?> breakers;

    AccountController(Customers customers, CircuitBreakerFactory<?, ?> breakers) {
        this.customers = customers;
        this.breakers = breakers;
    }

    @GetMapping("/{id}")
    AccountView one(@PathVariable String id) {
        Account account = accounts.get(id);
        if (account == null) throw new ResponseStatusException(HttpStatus.NOT_FOUND);
        return breakers.create("customers").run(
            () -> new AccountView(account, customers.find(account.customerId()), true),
            error -> new AccountView(account, null, false));
    }
}
