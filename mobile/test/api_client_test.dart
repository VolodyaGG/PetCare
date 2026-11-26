import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:petcare/core/network/api_client.dart';
import 'package:petcare/core/network/backend_health.dart';

void main() {
  final baseUrl = Uri.parse('http://127.0.0.1:8000');

  ApiClient clientWith(MockClientHandler handler) {
    final transport = MockClient(handler);
    addTearDown(transport.close);
    return ApiClient(baseUrl: baseUrl, transport: transport);
  }

  test('checks backend readiness at the server root', () async {
    final client = clientWith((request) async {
      expect(request.method, 'GET');
      expect(request.url, baseUrl.resolve('/health'));
      expect(request.headers['accept'], 'application/json');
      return http.Response('{"status":"ok","database":"ok"}', 200);
    });

    await BackendHealth(client).check();
  });

  test(
    'retains the backend error code, HTTP status and UTF-8 message',
    () async {
      final client = clientWith((request) async {
        return http.Response.bytes(
          utf8.encode(
            '{"error":{"code":"database_unavailable","message":"База недоступна"}}',
          ),
          503,
        );
      });

      await expectLater(
        BackendHealth(client).check(),
        throwsA(
          isA<ApiException>()
              .having((error) => error.statusCode, 'statusCode', 503)
              .having((error) => error.code, 'code', 'database_unavailable')
              .having((error) => error.message, 'message', 'База недоступна'),
        ),
      );
    },
  );

  test('rejects unexpected health responses', () async {
    final client = clientWith((request) async {
      return http.Response('{"status":"ok"}', 200);
    });

    await expectLater(
      BackendHealth(client).check(),
      throwsA(
        isA<ApiException>().having(
          (error) => error.code,
          'code',
          'invalid_response',
        ),
      ),
    );
  });

  test('sends JSON and supports an empty response body', () async {
    final client = clientWith((request) async {
      expect(request.method, 'PATCH');
      expect(request.url, baseUrl.resolve('/api/v1/pets/demo'));
      expect(jsonDecode(request.body), {'name': 'Барсик'});
      return http.Response('', 204);
    });

    expect(
      await client.requestJson(
        'PATCH',
        '/api/v1/pets/demo',
        body: {'name': 'Барсик'},
      ),
      isNull,
    );
  });
}
