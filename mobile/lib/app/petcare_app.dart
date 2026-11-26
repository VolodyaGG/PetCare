import 'package:material_ui/material_ui.dart';

import '../features/pets/pets_screen.dart';
import '../features/settings/settings_screen.dart';
import '../features/tasks/tasks_screen.dart';

class PetCareApp extends StatelessWidget {
  const PetCareApp({super.key, required this.checkBackend});

  final Future<void> Function() checkBackend;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PetCare',
      theme: ThemeData(colorSchemeSeed: const Color(0xFF176C5A)),
      home: _HomeShell(checkBackend: checkBackend),
    );
  }
}

enum _Tab {
  pets('Питомцы', Icons.pets),
  tasks('Задачи', Icons.checklist),
  settings('Настройки', Icons.settings_outlined);

  const _Tab(this.label, this.icon);

  final String label;
  final IconData icon;
}

class _HomeShell extends StatefulWidget {
  const _HomeShell({required this.checkBackend});

  final Future<void> Function() checkBackend;

  @override
  State<_HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<_HomeShell> {
  _Tab _selected = _Tab.pets;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(_selected.label)),
      body: SafeArea(
        child: IndexedStack(
          index: _selected.index,
          children: [
            const PetsScreen(),
            const TasksScreen(),
            SettingsScreen(checkBackend: widget.checkBackend),
          ],
        ),
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selected.index,
        onDestinationSelected: (index) =>
            setState(() => _selected = _Tab.values[index]),
        destinations: [
          for (final tab in _Tab.values)
            NavigationDestination(icon: Icon(tab.icon), label: tab.label),
        ],
      ),
    );
  }
}
