import 'dart:async';

class ApiService {
  // TODO: replace with real backend URL when Jenifer's backend is ready
  static const String baseUrl = 'http://localhost:8000';

  // Simulates POST /api/transaction
  Future<bool> sendTransaction({
    required String sender,
    required String receiver,
    required String amount,
  }) async {
    // TODO: replace this block with real HTTP POST when backend is ready
    // Real code will look like this:
    // final response = await http.post(
    //   Uri.parse('$baseUrl/api/transaction'),
    //   headers: {'Content-Type': 'application/json'},
    //   body: jsonEncode({
    //     'sender': sender,
    //     'receiver': receiver,
    //     'amount': amount,
    //   }),
    // );
    // return response.statusCode == 200;

    // MOCK: simulate 2 second backend processing
    await Future.delayed(const Duration(seconds: 2));
    return true; // always succeeds in mock mode
  }

  // Simulates WebSocket ws://localhost:8000/ws/app
  Stream<String> listenForCompletion() {
    // TODO: replace this block with real WebSocket when backend is ready
    // Real code will look like this:
    // final channel = WebSocketChannel.connect(
    //   Uri.parse('ws://localhost:8000/ws/app'),
    // );
    // return channel.stream.map((event) => event.toString());

    // MOCK: simulate backend sending "complete" after 3 seconds
    final controller = StreamController<String>();
    Future.delayed(const Duration(seconds: 3), () {
      controller.add('complete');
      controller.close();
    });
    return controller.stream;
  }
}