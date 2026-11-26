import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

final class ApiClient {
  ApiClient({
    required Uri baseUrl,
    required this._transport,
    this._timeout = const Duration(seconds: 10),
  }) : _baseUrl = baseUrl {
    if (!['http', 'https'].contains(baseUrl.scheme) ||
        baseUrl.host.isEmpty ||
        baseUrl.userInfo.isNotEmpty ||
        (baseUrl.path.isNotEmpty && baseUrl.path != '/') ||
        baseUrl.hasQuery ||
        baseUrl.hasFragment) {
      throw ArgumentError.value(baseUrl, 'baseUrl', 'Expected an HTTP origin');
    }
  }

  final Uri _baseUrl;
  final http.Client _transport;
  final Duration _timeout;

  Future<Object?> requestJson(
    String method,
    String path, {
    Map<String, String>? queryParameters,
    Object? body,
  }) async {
    final endpoint = Uri.parse(path);
    if (!path.startsWith('/') ||
        endpoint.hasAuthority ||
        endpoint.hasQuery ||
        endpoint.hasFragment ||
        path.contains('\\')) {
      throw ArgumentError.value(path, 'path', 'Expected an absolute API path');
    }
    final uri = _baseUrl
        .resolveUri(endpoint)
        .replace(queryParameters: queryParameters);
    final abort = Completer<void>();
    final request = http.AbortableRequest(
      method,
      uri,
      abortTrigger: abort.future,
    )..followRedirects = false;
    request.headers['Accept'] = 'application/json';
    if (body != null) {
      request.headers['Content-Type'] = 'application/json; charset=utf-8';
      request.body = jsonEncode(body);
    }

    final http.Response response;
    try {
      response = await _transport
          .send(request)
          .then(http.Response.fromStream)
          .timeout(
            _timeout,
            onTimeout: () {
              abort.complete();
              throw const ApiException('timeout', 'Request timed out');
            },
          );
    } on http.ClientException {
      throw const ApiException('network_error', 'Could not reach the server');
    }

    final statusCode = response.statusCode;
    Object? data;
    try {
      if (response.bodyBytes.isNotEmpty) {
        data = jsonDecode(utf8.decode(response.bodyBytes));
      }
    } on FormatException {
      if (statusCode >= 200 && statusCode < 300) {
        throw ApiException(
          'invalid_response',
          'Expected a JSON response',
          statusCode: statusCode,
        );
      }
    }
    if (statusCode >= 200 && statusCode < 300) {
      return data;
    }

    if (data case {
      'error':
          final Map<String, dynamic> error &&
          {'code': final String code, 'message': final String message},
    }) {
      throw ApiException(
        code,
        message,
        statusCode: statusCode,
        details: error['details'],
      );
    }
    throw ApiException(
      'http_error',
      'Server returned an HTTP error',
      statusCode: statusCode,
    );
  }
}

final class ApiException implements Exception {
  const ApiException(this.code, this.message, {this.statusCode, this.details});

  final String code;
  final String message;
  final int? statusCode;
  final Object? details;

  @override
  String toString() => 'ApiException($code, HTTP $statusCode): $message';
}
