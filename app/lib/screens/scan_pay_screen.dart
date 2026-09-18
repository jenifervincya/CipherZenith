import 'package:flutter/material.dart';
import 'send_money_screen.dart';

class ScanPayScreen extends StatelessWidget {
  const ScanPayScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0F172A),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            padding: const EdgeInsets.only(top: 50, left: 20, right: 20, bottom: 20),
            color: const Color(0xFF0F172A),
            child: Row(
              children: [
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.arrow_back, color: Colors.white, size: 22),
                  ),
                ),
                const SizedBox(width: 16),
                const Text(
                  'Scan & Pay',
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold, color: Colors.white),
                ),
              ],
            ),
          ),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text(
                  'Point camera at QR code',
                  style: TextStyle(color: Colors.white70, fontSize: 14),
                ),
                const SizedBox(height: 30),
                // Fake scanner UI
                Stack(
                  alignment: Alignment.center,
                  children: [
                    Container(
                      width: 260,
                      height: 260,
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.05),
                        borderRadius: BorderRadius.circular(20),
                      ),
                    ),
                    // Corner borders
                    Positioned(
                      top: 0,
                      left: 0,
                      child: _corner(top: true, left: true),
                    ),
                    Positioned(
                      top: 0,
                      right: 0,
                      child: _corner(top: true, left: false),
                    ),
                    Positioned(
                      bottom: 0,
                      left: 0,
                      child: _corner(top: false, left: true),
                    ),
                    Positioned(
                      bottom: 0,
                      right: 0,
                      child: _corner(top: false, left: false),
                    ),
                    // Scanner line
                    Container(
                      width: 220,
                      height: 2,
                      color: const Color(0xFF2563EB).withOpacity(0.8),
                    ),
                    const Icon(Icons.qr_code_scanner, size: 80, color: Colors.white24),
                  ],
                ),
                const SizedBox(height: 40),
                const Text(
                  'OR',
                  style: TextStyle(color: Colors.white54, fontSize: 14),
                ),
                const SizedBox(height: 20),
                GestureDetector(
                  onTap: () => Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(builder: (_) => const SendMoneyScreen()),
                  ),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 14),
                    decoration: BoxDecoration(
                      color: const Color(0xFF2563EB),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: const Text(
                      'Enter details manually',
                      style: TextStyle(
                        color: Colors.white,
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _corner({required bool top, required bool left}) {
    return Container(
      width: 40,
      height: 40,
      decoration: BoxDecoration(
        border: Border(
          top: top ? const BorderSide(color: Color(0xFF2563EB), width: 3) : BorderSide.none,
          bottom: !top ? const BorderSide(color: Color(0xFF2563EB), width: 3) : BorderSide.none,
          left: left ? const BorderSide(color: Color(0xFF2563EB), width: 3) : BorderSide.none,
          right: !left ? const BorderSide(color: Color(0xFF2563EB), width: 3) : BorderSide.none,
        ),
        borderRadius: BorderRadius.only(
          topLeft: top && left ? const Radius.circular(8) : Radius.zero,
          topRight: top && !left ? const Radius.circular(8) : Radius.zero,
          bottomLeft: !top && left ? const Radius.circular(8) : Radius.zero,
          bottomRight: !top && !left ? const Radius.circular(8) : Radius.zero,
        ),
      ),
    );
  }
}