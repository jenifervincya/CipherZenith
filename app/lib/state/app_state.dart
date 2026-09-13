import 'package:flutter/material.dart';

class Transaction {
  final String id;
  final String receiver;
  final double amount;
  final DateTime time;
  final bool success;

  Transaction({
    required this.id,
    required this.receiver,
    required this.amount,
    required this.time,
    required this.success,
  });
}

class AppState extends ChangeNotifier {
  double balance = 10000.0;
  List<Transaction> transactions = [];

  void deductBalance(String receiver, double amount) {
    balance -= amount;
    transactions.insert(
      0,
      Transaction(
        id: 'TXN${DateTime.now().millisecondsSinceEpoch}',
        receiver: receiver,
        amount: amount,
        time: DateTime.now(),
        success: true,
      ),
    );
    notifyListeners();
  }

  void addMoney(double amount) {
    balance += amount;
    notifyListeners();
  }
}