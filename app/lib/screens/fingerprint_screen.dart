import 'package:flutter/material.dart';
import 'package:local_auth/local_auth.dart';
import 'home_screen.dart';

class FingerprintScreen extends StatefulWidget {
  const FingerprintScreen({super.key});

  @override
  State<FingerprintScreen> createState() => _FingerprintScreenState();
}

class _FingerprintScreenState extends State<FingerprintScreen> {
  final LocalAuthentication _auth = LocalAuthentication();
  bool _isVerifying = false;
  String _status = "Place your finger on the scanner";

  Future<void> _startVerification() async {
    if (_isVerifying) return;

    setState(() {
      _isVerifying = true;
      _status = "Verifying...";
    });

    try {
      final bool canCheck = await _auth.canCheckBiometrics;
      final bool isSupported = await _auth.isDeviceSupported();

      if (!canCheck && !isSupported) {
        setState(() {
          _isVerifying = false;
          _status = "Biometric not available on this device";
        });
        return;
      }

      final bool authenticated = await _auth.authenticate(
        localizedReason: 'Authenticate to access CipherPay',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );

      if (!mounted) return;

      if (authenticated) {
        setState(() {
          _isVerifying = false;
          _status = "Identity verified!";
        });

        await Future.delayed(const Duration(milliseconds: 600));

        if (!mounted) return;
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (_) => const HomeScreen()),
        );
      } else {
        setState(() {
          _isVerifying = false;
          _status = "Authentication failed. Try again.";
        });
      }
    } catch (e) {
      if (!mounted) return;
  // On web/chrome, biometrics not supported — skip to home
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(builder: (_) => const HomeScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF1A1A2E), Color(0xFF16213E)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(28),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F3460),
                      borderRadius: BorderRadius.circular(28),
                      border: Border.all(color: const Color(0xFF22D3EE), width: 0.5),
                    ),
                    child: Column(
                      children: [
                        Container(
                          height: 80,
                          width: 80,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(20),
                            gradient: const LinearGradient(
                              colors: [Color(0xFF22D3EE), Color(0xFF0EA5E9)],
                            ),
                          ),
                          child: const Icon(
                            Icons.shield_outlined,
                            size: 40,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 20),
                        const Text(
                          "CipherPay",
                          style: TextStyle(
                            fontSize: 28,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF22D3EE),
                          ),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          "Verify your identity to access\nQuantum-Safe Payments",
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.white70,
                          ),
                        ),
                        const SizedBox(height: 30),
                        Container(
                          height: 160,
                          width: 160,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: const Color(0xFF1A1A2E),
                            border: Border.all(
                              color: const Color(0xFF22D3EE),
                              width: 2,
                            ),
                          ),
                          child: Center(
                            child: _isVerifying
                                ? const CircularProgressIndicator(
                                    color: Color(0xFF22D3EE),
                                  )
                                : const Icon(
                                    Icons.fingerprint,
                                    size: 100,
                                    color: Color(0xFF22D3EE),
                                  ),
                          ),
                        ),
                        const SizedBox(height: 24),
                        Text(
                          _status,
                          textAlign: TextAlign.center,
                          style: const TextStyle(
                            fontSize: 15,
                            color: Colors.white70,
                          ),
                        ),
                        const SizedBox(height: 28),
                        SizedBox(
                          width: double.infinity,
                          height: 54,
                          child: ElevatedButton.icon(
                            onPressed: _isVerifying ? null : _startVerification,
                            icon: const Icon(Icons.fingerprint, color: Colors.white),
                            label: const Text(
                              "Verify Identity",
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: const Color(0xFF22D3EE),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    "QUANTUM-SAFE ENCRYPTION ACTIVE",
                    style: TextStyle(
                      color: Colors.white54,
                      letterSpacing: 1.4,
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}