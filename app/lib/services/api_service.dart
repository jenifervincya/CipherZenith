import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

class ApiService {
  // IMPORTANT: Replace with Jeni's current local IP on demo day
  // Run `ipconfig` on Jeni's laptop to get the current address
  static const String baseUrl = 'http://10.165.165.212:8000';
  static const String wsUrl = 'ws://10.165.165.212:8000/ws/app';

  Future<bool> sendTransaction({
    required String sender,
    required String receiver,
    required String amount,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/api/transaction'),
        headers: {'Content-Type': 'application/json'},
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