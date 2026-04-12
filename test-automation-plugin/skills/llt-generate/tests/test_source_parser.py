#!/usr/bin/env python3
"""
Unit tests for source_parser.py

Tests clang AST parsing, regex fallback, and method extraction accuracy.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import source_parser


class TestRegexMethodExtraction(unittest.TestCase):
    """Test regex-based method extraction (fallback mode)."""

    def test_simple_method(self):
        """Test extraction of simple method."""
        header_content = """
        class MyClass {
        public:
            int GetValue() const;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'GetValue')
            self.assertEqual(methods[0]['return_type'], 'int')
            self.assertEqual(len(methods[0]['params']), 0)
            self.assertTrue(methods[0]['is_const'])
            self.assertFalse(methods[0]['is_virtual'])
        finally:
            header_path.unlink()

    def test_method_with_parameters(self):
        """Test extraction of method with parameters."""
        header_content = """
        class MyClass {
        public:
            void SetValue(int Value, const FString& Name);
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'SetValue')
            self.assertEqual(methods[0]['return_type'], 'void')
            self.assertEqual(len(methods[0]['params']), 2)
            self.assertEqual(methods[0]['params'][0]['type'], 'int')
            self.assertEqual(methods[0]['params'][0]['name'], 'Value')
            self.assertEqual(methods[0]['params'][1]['type'], 'const FString&')
            self.assertEqual(methods[0]['params'][1]['name'], 'Name')
        finally:
            header_path.unlink()

    def test_virtual_method(self):
        """Test extraction of virtual method."""
        header_content = """
        class MyClass {
        public:
            virtual void Execute() override;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'Execute')
            self.assertTrue(methods[0]['is_virtual'])
            self.assertFalse(methods[0]['is_pure_virtual'])
        finally:
            header_path.unlink()

    def test_pure_virtual_method(self):
        """Test extraction of pure virtual method."""
        header_content = """
        class IMyInterface {
        public:
            virtual int GetValue() const = 0;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'GetValue')
            self.assertTrue(methods[0]['is_virtual'])
            self.assertTrue(methods[0]['is_pure_virtual'])
            self.assertTrue(methods[0]['is_const'])
        finally:
            header_path.unlink()

    def test_ufunction_method(self):
        """Test extraction of UFUNCTION method."""
        header_content = """
        class UMyClass {
        public:
            UFUNCTION(BlueprintCallable, Category="MyCategory")
            void BlueprintMethod();
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'BlueprintMethod')
            self.assertTrue(methods[0]['has_ufunction'])
        finally:
            header_path.unlink()

    def test_template_method(self):
        """Test extraction of template method."""
        header_content = """
        class MyClass {
        public:
            template<typename T>
            T GetValue() const;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'GetValue')
            self.assertTrue(methods[0]['is_template'])
        finally:
            header_path.unlink()

    def test_multiple_methods(self):
        """Test extraction of multiple methods."""
        header_content = """
        class MyClass {
        public:
            int GetValue() const;
            void SetValue(int Value);
            virtual void Execute() = 0;
            static MyClass* Create();
        private:
            void InternalMethod();
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 5)
            method_names = [m['name'] for m in methods]
            self.assertIn('GetValue', method_names)
            self.assertIn('SetValue', method_names)
            self.assertIn('Execute', method_names)
            self.assertIn('Create', method_names)
            self.assertIn('InternalMethod', method_names)
        finally:
            header_path.unlink()

    def test_method_with_template_parameters(self):
        """Test extraction of method with template type parameters."""
        header_content = """
        class MyClass {
        public:
            void ProcessArray(TArray<int> Items, TMap<FString, int> Values);
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'ProcessArray')
            self.assertEqual(len(methods[0]['params']), 2)
            self.assertEqual(methods[0]['params'][0]['type'], 'TArray<int>')
            self.assertEqual(methods[0]['params'][0]['name'], 'Items')
            self.assertEqual(methods[0]['params'][1]['type'], 'TMap<FString, int>')
            self.assertEqual(methods[0]['params'][1]['name'], 'Values')
        finally:
            header_path.unlink()

    def test_method_with_default_parameters(self):
        """Test extraction of method with default parameter values."""
        header_content = """
        class MyClass {
        public:
            void SetValue(int Value = 0, bool bFlag = true);
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'SetValue')
            self.assertEqual(len(methods[0]['params']), 2)
            self.assertEqual(methods[0]['params'][0]['name'], 'Value')
            self.assertEqual(methods[0]['params'][1]['name'], 'bFlag')
        finally:
            header_path.unlink()

    def test_comments_removed(self):
        """Test that comments are properly removed before parsing."""
        header_content = """
        class MyClass {
        public:
            // This is a comment
            int GetValue() const; // Inline comment
            /* Multi-line
               comment */
            void SetValue(int Value);
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            self.assertEqual(len(methods), 2)
            method_names = [m['name'] for m in methods]
            self.assertIn('GetValue', method_names)
            self.assertIn('SetValue', method_names)
        finally:
            header_path.unlink()

    def test_constructor_destructor_skipped(self):
        """Test that constructors and destructors are skipped."""
        header_content = """
        class MyClass {
        public:
            MyClass();
            ~MyClass();
            int GetValue() const;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            # Only GetValue should be extracted (constructors/destructors skipped)
            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'GetValue')
        finally:
            header_path.unlink()


class TestClangMethodExtraction(unittest.TestCase):
    """Test clang AST-based method extraction (primary mode)."""

    def setUp(self):
        """Check if clang is available before running tests."""
        if not source_parser.CLANG_AVAILABLE:
            self.skipTest("libclang not available")

    def test_clang_available(self):
        """Test that clang bindings are available."""
        self.assertTrue(source_parser.CLANG_AVAILABLE)

    def test_simple_method_with_clang(self):
        """Test extraction of simple method using clang."""
        header_content = """
        class MyClass {
        public:
            int GetValue() const;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            # Create a minimal compilation database
            compdb_dir = header_path.parent
            compdb_content = [
                {
                    "directory": str(compdb_dir),
                    "command": f"clang++ -c {header_path}",
                    "file": str(header_path)
                }
            ]

            import json
            compdb_path = compdb_dir / "compile_commands.json"
            with open(compdb_path, 'w', encoding='utf-8') as f:
                json.dump(compdb_content, f)

            methods = source_parser.extract_methods_with_clang(header_path, compdb_dir)

            if methods is not None:
                self.assertEqual(len(methods), 1)
                self.assertEqual(methods[0]['name'], 'GetValue')
                self.assertEqual(methods[0]['return_type'], 'int')
                self.assertTrue(methods[0]['is_const'])
                # Check that mangled name is present (key feature of clang)
                self.assertIn('mangled_name', methods[0])
        finally:
            header_path.unlink()
            if compdb_path.exists():
                compdb_path.unlink()


class TestAutoFallback(unittest.TestCase):
    """Test automatic fallback from clang to regex."""

    def test_fallback_when_no_compdb(self):
        """Test that regex is used when no compilation database provided."""
        header_content = """
        class MyClass {
        public:
            int GetValue() const;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            # Call without compilation database
            methods = source_parser.extract_method_signatures(header_path, compdb_path=None)

            # Should fall back to regex
            self.assertEqual(len(methods), 1)
            self.assertEqual(methods[0]['name'], 'GetValue')
            # Regex mode doesn't have mangled names
            self.assertNotIn('mangled_name', methods[0])
        finally:
            header_path.unlink()


class TestParameterParsing(unittest.TestCase):
    """Test parameter parsing edge cases."""

    def test_split_params_smart_simple(self):
        """Test smart parameter splitting with simple types."""
        params_str = "int a, float b, double c"
        params = source_parser._split_params_smart(params_str)

        self.assertEqual(len(params), 3)
        self.assertEqual(params[0], "int a")
        self.assertEqual(params[1], "float b")
        self.assertEqual(params[2], "double c")

    def test_split_params_smart_templates(self):
        """Test smart parameter splitting with template types."""
        params_str = "TArray<int> Items, TMap<FString, int> Values"
        params = source_parser._split_params_smart(params_str)

        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "TArray<int> Items")
        self.assertEqual(params[1], "TMap<FString, int> Values")

    def test_split_params_smart_nested_templates(self):
        """Test smart parameter splitting with nested templates."""
        params_str = "TArray<TSharedPtr<FMyClass>> Items"
        params = source_parser._split_params_smart(params_str)

        self.assertEqual(len(params), 1)
        self.assertEqual(params[0], "TArray<TSharedPtr<FMyClass>> Items")

    def test_parse_parameters_with_references(self):
        """Test parameter parsing with references and pointers."""
        params_str = "const FString& Name, int* Count, MyClass** PPObject"
        params = source_parser._parse_parameters(params_str)

        self.assertEqual(len(params), 3)
        self.assertEqual(params[0]['type'], 'const FString&')
        self.assertEqual(params[0]['name'], 'Name')
        self.assertEqual(params[1]['type'], 'int*')
        self.assertEqual(params[1]['name'], 'Count')
        self.assertEqual(params[2]['type'], 'MyClass**')
        self.assertEqual(params[2]['name'], 'PPObject')


class TestCommentRemoval(unittest.TestCase):
    """Test C++ comment removal."""

    def test_remove_single_line_comments(self):
        """Test removal of single-line comments."""
        content = """
        int value; // This is a comment
        // Full line comment
        float f;
        """

        cleaned = source_parser._remove_cpp_comments(content)

        self.assertNotIn('//', cleaned)
        self.assertIn('int value;', cleaned)
        self.assertIn('float f;', cleaned)

    def test_remove_multi_line_comments(self):
        """Test removal of multi-line comments."""
        content = """
        int value;
        /* This is a
           multi-line
           comment */
        float f;
        """

        cleaned = source_parser._remove_cpp_comments(content)

        self.assertNotIn('/*', cleaned)
        self.assertNotIn('*/', cleaned)
        self.assertIn('int value;', cleaned)
        self.assertIn('float f;', cleaned)


if __name__ == '__main__':
    unittest.main()
