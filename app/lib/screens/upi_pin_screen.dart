import 'package:flutter/material.dart';

class UpiPinScreen extends StatefulWidget {
  final VoidCallback onSuccess;

  const UpiPinScreen({super.key, required this.onSuccess});

  @override
  State<UpiPinScreen> createState() => _UpiPinScreenState();
}

class _UpiPinScreenState extends State<UpiPinScreen> {
  String _pin = '';
  List<String> _keys = [];

  @override
  void initState() {
    super.initState();
    _shuffleKeys();
  }

  void _shuffleKeys() {
    _keys = ['1','2','3','4','5','6','7','8','9','⌫','0','✓'];
    final digits = _keys.sublist(0, 9);
    digits.shuffle();
    _keys = [...digits, '⌫', '0', '✓'];
    setState(() {});
  }

  void _onKeyTap(String key) {
    if (key == '⌫') {
      if (_pin.isNotEmpty) {
        setState(() => _pin = _pin.substring(0, _pin.length - 1));
      }
    } else if (key == '✓') {
      if (_pin.length >= 4) {
        // PIN accepted — proceed
        widget.onSuccess();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Enter at least 4 digits')),
        );
      }
    } else {
      if (_pin.length < 6) {
        setState(() => _pin += key);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.white,
      body: Column(
        children: [
          // Blue header
          Container(
            width: double.infinity,
            padding: const EdgeInsets.only(top: 50, left: 20, right: 20, bottom: 30),
            decoration: const BoxDecoration(
              color: Color(0xFF2563EB),
              borderRadius: BorderRadius.only(
                bottomLeft: Radius.circular(30),
                bottomRight: Radius.circular(30),
              ),
            ),
            child: Row(
              children: [
                GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Icon(Icons.arrow_back, color: Colors.white, size: 22),
                  ),
                ),
                const SizedBox(width: 16),
                const Text(
                  'Enter UPI PIN',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
              ],
            ),
          ),

          const SizedBox(height: 40),

          const Text(
            'Enter your UPI PIN to confirm payment',
            style: TextStyle(fontSize: 14, color: Colors.grey),
          ),

          const SizedBox(height: 30),

          // PIN dots
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(6, (index) {
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 8),
                width: 16,
                height: 16,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: index < _pin.length
                      ? const Color(0xFF2563EB)
                      : const Color(0xFFE5E7EB),
                ),
              );
            }),
          ),

          

          
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 40),
            child: GridView.builder(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 3,
                childAspectRatio: 1.8,
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
              ),
              itemCount: _keys.length,
              itemBuilder: (context, index) {
                final key = _keys[index];
                final isConfirm = key == '✓';
                final isDelete = key == '⌫';

                return GestureDetector(
                  onTap: () => _onKeyTap(key),
                  child: Container(
                    decoration: BoxDecoration(
                      color: isConfirm
                          ? const Color(0xFF2563EB)
                          : isDelete
                              ? const Color(0xFFFEE2E2)
                              : const Color(0xFFEFF6FF),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: isConfirm
                            ? const Color(0xFF2563EB)
                            : const Color(0xFFE5E7EB),
                      ),
                    ),
                    child: Center(
                      child: Text(
                        key,
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: isConfirm
                              ? Colors.white
                              : isDelete
                                  ? const Color(0xFFEF4444)
                                  : const Color(0xFF0F172A),
                        ),
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}