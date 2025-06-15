Java_sourceCode="""
public class OrderProcessor {
        private PaymentService paymentService;
        private InventoryService inventoryService;

        public OrderProcessor(PaymentService paymentService, InventoryService inventoryService) {
            this.paymentService = paymentService;
            this.inventoryService = inventoryService;
        }

        public boolean processOrder(String orderId) {
            boolean paymentSuccess = paymentService.charge(orderId);
            if (!paymentSuccess) {
                return false;
            }
            inventoryService.reserveItems(orderId);
            return true;
        }

        public void cancelOrder(String orderId) {
            paymentService.refund(orderId);
            inventoryService.releaseItems(orderId);
        }

        public String getOrderStatus(String orderId) {
            return "Processed";
        }
    }
"""