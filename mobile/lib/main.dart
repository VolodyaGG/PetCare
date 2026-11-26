import 'package:http/http.dart' as http;
import 'package:material_ui/material_ui.dart';

import 'app/petcare_app.dart';
import 'core/network/api_client.dart';
import 'core/network/backend_health.dart';

void main() {
  runApp(const _Bootstrap());
}

class _Bootstrap extends StatefulWidget {
  const _Bootstrap();

  @override
  State<_Bootstrap> createState() => _BootstrapState();
}

class _BootstrapState extends State<_Bootstrap> {
  static const _baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000',
  );

  final _transport = http.Client();
  late final _backendHealth = BackendHealth(
    ApiClient(baseUrl: Uri.parse(_baseUrl), transport: _transport),
  );

  @override
  Widget build(BuildContext context) {
    return PetCareApp(checkBackend: _backendHealth.check);
  }

  @override
  void dispose() {
    _transport.close();
    super.dispose();
  }
}
