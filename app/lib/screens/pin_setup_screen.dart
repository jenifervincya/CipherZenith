import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'home_screen.dart';

class PinSetupScreen extends StatefulWidget {
  const PinSetupScreen({super.key});

  @override
  State<PinSetupScreen> createState() => _PinSetupScreenState();
}

class _PinSetupScreenState extends State<PinSetupScreen> {
  String _pin = '';
  String _confirmPin = '';
  bool _isConfirming = false;
  List<String> _keys = [];

  @override
  void initState() {
    super.initState();
    _shuffleKeys();
  }

  void _shuffleKeys() {
    final digits = ['1','2','3','4','5','6','7','8','9'];
    digits.shuffle();
    _keys = [...digits, '⌫', '0', '✓'];
    setState(() {});
  }

  void _onKeyTap(String key) {
    if (key == '⌫') {
      if (!_isConfirming && _pin.isNotEmpty) {
        setState(() => _pin = _pin.substring(0, _pin.length - 1));
      } else if (_isConfirming && _confirmPin.isNotEmpty) {
        setState(() => _confirmPin = _confirmPin.substring(0, _confirmPin.length - 1));
      }
    } else if (key == '✓') {
      if (!_isConfirming) {
        if (_pin.length >= 4) {
          setState(() {
            _isConfirming = true;
            _shuffleKeys();
          });
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Enter at least 4 digits')),
          );
        }
      } else {
        if (_confirmPin == _pin) {
          _savePin();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('PINs do not match. Try again.')),
          );
          setState(() {
            _confirmPin = '';
            _pin = '';
            _isConfirming = false;
            _shuffleKeys();
          });
        }
      }
    } else {
      if (!_isConfirming && _pin.length < 6) {
        setState(() => _pin += key);
      } else if (_isConfirming && _confirmPin.length < 6) {
        setState(() => _confirmPin += key);
      }
    }
  }

  Future<void> _savePin() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('app_pin', _pin);
    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const HomeScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final currentPin = _isConfirming ? _confirmPin : _pin;

    return Scaffold(
      backgroundColor: Colors.white,
      body: Column(
        children: [
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
            child: Text(
              _isConfirming ? 'Confirm PIN' : 'Set Your PIN',
              style: const TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 40),
          Text(
            _isConfirming ? 'Re-enter your PIN to confirm' : 'Create a 4-6 digit PIN',
            style: const TextStyle(fontSize: 14, color: Colors.grey),
          ),
          const SizedBox(height: 30),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(6, (index) {
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 8),
                width: 16,
                height: 16,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: index < currentPin.length
                      ? const Color(0xFF2563EB)
                      : const Color(0xFFE5E7EB),
                ),
              );
            }),
          ),
          const SizedBox(height: 40),
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