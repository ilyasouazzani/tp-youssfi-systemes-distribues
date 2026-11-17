package ma.enset;
import java.util.List;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

@SpringBootApplication
public class Application {
    public static void main(String[] args) { SpringApplication.run(Application.class, args); }
}

@RestController
@RequestMapping("/customers")
class CustomerController {
    private final List<Customer> customers = List.of(new Customer(1, "Client Démo"),
                                                     new Customer(2, "Cliente Démo"));
    @GetMapping
    List<Customer> all() { return customers; }

    @GetMapping("/{id}")
    Customer one(@PathVariable long id) {
        return customers.stream().filter(customer -> customer.id() == id).findFirst()
            .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND));
    }
}
record Customer(long id, String name) {}
