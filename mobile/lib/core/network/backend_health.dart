import 'api_client.dart';

final class BackendHealth {
  const BackendHealth(this._client);

  final ApiClient _client;

  Future<void> check() async {
    final response = await _client.requestJson('GET', '/health');
    if (response case {'status': 'ok', 'database': 'ok'}) {
      return;
    }
    throw const ApiException('invalid_response', 'Unexpected health response');
  }
}
