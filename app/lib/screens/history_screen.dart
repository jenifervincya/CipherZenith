import 'package:flutter/material.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  // Dummy transaction data for demo
  final List<Map<String, String>> _transactions = const [
    {'receiver': 'Mugunthan', 'amount': '500'},
    {'receiver': 'Jenifer', 'amount': '1000'},
    {'receiver': 'Mohamed', 'amount': '250'},
    {'receiver': 'Rithanya', 'amount': '750'},
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: const Color(0xFF0D1117),
        title: const Text(
          'Transaction History',
          style: TextStyle(color: Color(0xFF22D3EE)),
        ),
        iconTheme: const IconThemeData(color: Color(0xFF22D3EE)),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.all(20),
        itemCount: _transactions.length,
        separatorBuilder: (_, __) => const SizedBox(height: 12),
        itemBuilder: (context, index) {
          final tx = _transactions[index];
          return Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: const Color(0xFF161B22),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: const Color(0xFF22D3EE),
                width: 0.5,
              ),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.lock,
                  color: Color(0xFF22D3EE),
                  size: 28,
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        tx['receiver']!,
                        style: const TextStyle(
                          fontSize: 16,
                          color: Colors.white,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      const Text(
                        'Secured',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.white38,
                        ),
                      ),
                    ],
                  ),
                ),
                Text(
                  '₹${tx['amount']}',
                  style: const TextStyle(
                    fontSize: 16,
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}