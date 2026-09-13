import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiService {
  static const String baseUrl = 'https://enviably-dab-progress.ngrok-free.dev';
  static const String wsUrl = 'wss://enviably-dab-progress.ngrok-free.dev/ws/app';

  Future<bool> sendTransaction({
    required String sender,
    required String receiver,
    required String amount,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/transaction'),
        headers:{
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true',
        },
        body: jsonEncode({
          'sender': sender,
          'receiver': receiver,
          'amount': double.parse(amount),
        }),
      );
      return response.statusCode == 200;
    } catch (e) {
      print('Transaction POST failed: $e');
      return false;
    }
  }

  StreamSubscription listenForCompletion({
    required Function(Map<String, dynamic> data) onComplete,
  }) {
    final channel = WebSocketChannel.connect(Uri.parse(wsUrl));
    return channel.stream.listen((message) {
      final data = jsonDecode(message);
      if (data['status'] == 'complete') {
        onComplete(data);
      }
    });
  }
}