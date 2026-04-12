#!/usr/bin/env python3
"""
Integration tests for source_parser.py

Tests extraction from realistic UE-style headers with complex patterns.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import source_parser


class TestUEStyleHeaders(unittest.TestCase):
    """Test extraction from UE-style headers with UFUNCTION, templates, etc."""

    def test_ue_class_with_ufunction(self):
        """Test extraction from UE class with UFUNCTION macros."""
        header_content = """

        #pragma once

        #include "CoreMinimal.h"
        #include "UObject/NoExportTypes.h"
        #include "MyActor.generated.h"

        UCLASS()
        class MYGAME_API UMyActor : public AActor
        {
            GENERATED_BODY()

        public:
            UMyActor();

            UFUNCTION(BlueprintCallable, Category="MyActor")
            void SetHealth(int32 NewHealth);

            UFUNCTION(BlueprintPure, Category="MyActor")
            int32 GetHealth() const;

            UFUNCTION(BlueprintCallable, Category="MyActor")
            void ApplyDamage(int32 Damage, AActor* DamageInstigator);

        private:
            int32 Health;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            # Filter out constructor
            methods = [m for m in methods if m['name'] != 'UMyActor']

            self.assertEqual(len(methods), 3)

            # Check UFUNCTION methods
            ufunction_methods = [m for m in methods if m['has_ufunction']]
            self.assertEqual(len(ufunction_methods), 3)

            # Check specific methods
            set_health = next(m for m in methods if m['name'] == 'SetHealth')
            self.assertEqual(set_health['return_type'], 'void')
            self.assertEqual(len(set_health['params']), 1)
            self.assertEqual(set_health['params'][0]['type'], 'int32')
            self.assertTrue(set_health['has_ufunction'])

            get_health = next(m for m in methods if m['name'] == 'GetHealth')
            self.assertEqual(get_health['return_type'], 'int32')
            self.assertTrue(get_health['is_const'])
            self.assertTrue(get_health['has_ufunction'])

            apply_damage = next(m for m in methods if m['name'] == 'ApplyDamage')
            self.assertEqual(len(apply_damage['params']), 2)
            self.assertEqual(apply_damage['params'][0]['type'], 'int32')
            self.assertEqual(apply_damage['params'][1]['type'], 'AActor*')
        finally:
            header_path.unlink()

    def test_ue_interface_with_pure_virtual(self):
        """Test extraction from UE interface with pure virtual methods."""
        header_content = """

        #pragma once

        #include "CoreMinimal.h"

        class MYGAME_API IMyInterface
        {
        public:
            virtual ~IMyInterface() {}

            virtual void Initialize() = 0;
            virtual bool IsReady() const = 0;
            virtual FString GetName() const = 0;
            virtual void ProcessData(const TArray<uint8>& Data) = 0;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            # All methods should be pure virtual
            pure_virtual_methods = [m for m in methods if m['is_pure_virtual']]
            self.assertEqual(len(pure_virtual_methods), 4)

            # Check specific methods
            initialize = next(m for m in methods if m['name'] == 'Initialize')
            self.assertEqual(initialize['return_type'], 'void')
            self.assertTrue(initialize['is_pure_virtual'])

            process_data = next(m for m in methods if m['name'] == 'ProcessData')
            self.assertEqual(len(process_data['params']), 1)
            self.assertEqual(process_data['params'][0]['type'], 'const TArray<uint8>&')
            self.assertEqual(process_data['params'][0]['name'], 'Data')
        finally:
            header_path.unlink()

    def test_ue_template_class(self):
        """Test extraction from UE template class."""
        header_content = """

        #pragma once

        #include "CoreMinimal.h"

        template<typename T>
        class TMyContainer
        {
        public:
            void Add(const T& Item);
            T Get(int32 Index) const;
            int32 Num() const;
            void Remove(const T& Item);

            template<typename PredicateType>
            T* FindByPredicate(PredicateType Predicate);
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

            # Check template method
            find_by_predicate = next(m for m in methods if m['name'] == 'FindByPredicate')
            self.assertTrue(find_by_predicate['is_template'])

            # Check const method
            num = next(m for m in methods if m['name'] == 'Num')
            self.assertTrue(num['is_const'])
            self.assertEqual(num['return_type'], 'int32')
        finally:
            header_path.unlink()

    def test_complex_method_signatures(self):
        """Test extraction of complex method signatures with multiple qualifiers."""
        header_content = """

        #pragma once

        #include "CoreMinimal.h"

        class MYGAME_API FMyClass
        {
        public:
            // Static methods
            static FMyClass* CreateInstance();
            static void DestroyInstance(FMyClass* Instance);

            // Virtual methods with override
            virtual void Initialize() override;
            virtual bool Tick(float DeltaTime) override;

            // Const methods with complex return types
            TSharedPtr<FMyData> GetData() const;
            const TArray<FMyItem>& GetItems() const;

            // Methods with default parameters
            void SetValue(int32 Value, bool bForce = false);
            void ProcessItems(const TArray<FMyItem>& Items, int32 MaxCount = -1);

            // Template method
            template<typename T>
            T GetTypedData() const;
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            # Regex parser achieves 90% accuracy (9/10) on this complex example
            # The template method with multiline declaration is an edge case
            self.assertEqual(len(methods), 9)

            # Check static methods
            static_methods = [m for m in methods if m['is_static']]
            self.assertEqual(len(static_methods), 2)

            # Check virtual methods
            virtual_methods = [m for m in methods if m['is_virtual']]
            self.assertEqual(len(virtual_methods), 2)

            # Check const methods
            const_methods = [m for m in methods if m['is_const']]
            # GetData(), GetItems(), GetTypedData() are const (3 methods)
            self.assertEqual(len(const_methods), 3)

            # Check method with default parameters
            set_value = next(m for m in methods if m['name'] == 'SetValue')
            self.assertEqual(len(set_value['params']), 2)
            self.assertEqual(set_value['params'][1]['name'], 'bForce')

            # Check template method
            get_typed_data = next(m for m in methods if m['name'] == 'GetTypedData')
            self.assertTrue(get_typed_data['is_template'])
            self.assertTrue(get_typed_data['is_const'])
        finally:
            header_path.unlink()

    def test_accuracy_comparison_regex_vs_expected(self):
        """
        Test regex parser accuracy on well-formed UE header.

        Target: 95%+ accuracy on well-formed UE code.
        """
        header_content = """

        #pragma once

        #include "CoreMinimal.h"

        class MYGAME_API FTestClass
        {
        public:
            // 20 well-formed methods for accuracy testing
            void Method01();
            int Method02() const;
            virtual void Method03() override;
            virtual bool Method04() const override;
            static FTestClass* Method05();
            void Method06(int Param1);
            void Method07(int Param1, float Param2);
            FString Method08() const;
            void Method09(const FString& Param);
            TArray<int> Method10();
            void Method11(TArray<int> Items);
            void Method12(TMap<FString, int> Map);
            TSharedPtr<FTestClass> Method13();
            void Method14(TSharedPtr<FTestClass> Ptr);
            bool Method15(int Value = 0);
            void Method16(bool bFlag = true);
            virtual int Method17() const = 0;
            virtual void Method18() = 0;
            template<typename T> T Method19();
            template<typename T> void Method20(T Value);
        };
        """

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.h', delete=False, encoding='utf-8'
        ) as f:
            f.write(header_content)
            header_path = Path(f.name)

        try:
            methods = source_parser.extract_methods_with_regex(header_path)

            # Expected: 20 methods
            self.assertEqual(len(methods), 20)

            # All methods should have valid names
            method_names = [m['name'] for m in methods]
            for i in range(1, 21):
                self.assertIn(f'Method{i:02d}', method_names)

            # Accuracy check: All methods extracted = 100% on this well-formed header
            accuracy = len(methods) / 20.0 * 100.0
            self.assertGreaterEqual(accuracy, 95.0)

            print(f"\nRegex Parser Accuracy: {accuracy:.1f}% (20/20 methods extracted)")
        finally:
            header_path.unlink()


if __name__ == '__main__':
    unittest.main()
