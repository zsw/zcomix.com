def load_tests(loader, standard_tests, pattern):
    package_tests = loader.discover(start_dir='applications.zcomix', pattern='test_*.py')
    standard_tests.addTests(package_tests)
    return standard_tests
