from rest_framework import serializers

from diary.models import DiaryEntry, PlannedMeal
from products.models import FoodProduct
from recipes.models import Recipe, RecipeIngredient


class FoodProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodProduct
        fields = (
            'id', 'name', 'brand', 'calories_per_100g',
            'protein_per_100g', 'fat_per_100g', 'carbs_per_100g',
            'fiber_per_100g', 'sugar_per_100g',
            'sodium_mg_per_100g', 'potassium_mg_per_100g',
            'is_public', 'tags', 'created_by',
        )
        read_only_fields = ('id', 'created_by')

    def validate(self, attrs):
        for field in (
            'calories_per_100g', 'protein_per_100g', 'fat_per_100g',
            'carbs_per_100g', 'fiber_per_100g', 'sugar_per_100g',
            'sodium_mg_per_100g', 'potassium_mg_per_100g',
        ):
            value = attrs.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({field: 'Значение не может быть отрицательным.'})
        return attrs


class RecipeIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = ('id', 'product', 'amount', 'unit', 'piece_grams', 'weight', 'grams', 'kcal', 'protein', 'fat', 'carbs')
        read_only_fields = ('id', 'grams', 'kcal', 'protein', 'fat', 'carbs')

    def validate_amount(self, value):
        if value < 0:
            raise serializers.ValidationError('Количество не может быть отрицательным.')
        return value


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(many=True)
    total_kcal = serializers.FloatField(read_only=True)
    total_protein = serializers.FloatField(read_only=True)
    total_fat = serializers.FloatField(read_only=True)
    total_carbs = serializers.FloatField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'servings', 'instructions', 'image', 'tags',
            'is_public', 'created_by', 'created_at', 'ingredients',
            'total_kcal', 'total_protein', 'total_fat', 'total_carbs',
        )
        read_only_fields = ('id', 'created_by', 'created_at')

    def validate_servings(self, value):
        if value <= 0:
            raise serializers.ValidationError('Количество порций должно быть больше нуля.')
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients', [])
        recipe = Recipe.objects.create(**validated_data)
        for item in ingredients:
            RecipeIngredient.objects.create(recipe=recipe, **item)
        return recipe

    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if ingredients is not None:
            instance.ingredients.all().delete()
            for item in ingredients:
                RecipeIngredient.objects.create(recipe=instance, **item)
        return instance


class DiaryEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = DiaryEntry
        fields = (
            'id', 'date', 'time', 'meal', 'product', 'recipe',
            'grams', 'servings', 'note',
            'total_kcal', 'total_protein', 'total_fat', 'total_carbs',
        )
        read_only_fields = (
            'id', 'total_kcal', 'total_protein', 'total_fat', 'total_carbs',
        )

    def validate(self, attrs):
        product = attrs.get('product', getattr(self.instance, 'product', None))
        recipe = attrs.get('recipe', getattr(self.instance, 'recipe', None))
        if bool(product) == bool(recipe):
            raise serializers.ValidationError('Выберите либо product, либо recipe.')
        if attrs.get('grams', getattr(self.instance, 'grams', 0)) < 0:
            raise serializers.ValidationError({'grams': 'Вес не может быть отрицательным.'})
        if attrs.get('servings', getattr(self.instance, 'servings', 0)) < 0:
            raise serializers.ValidationError({'servings': 'Количество порций не может быть отрицательным.'})
        return attrs


class PlannedMealSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True)
    kcal = serializers.FloatField(read_only=True)

    class Meta:
        model = PlannedMeal
        fields = (
            'id', 'date', 'time', 'meal_type', 'product', 'recipe',
            'grams', 'servings', 'note', 'done', 'name', 'kcal',
        )
        read_only_fields = ('id', 'name', 'kcal')

    def validate(self, attrs):
        product = attrs.get('product', getattr(self.instance, 'product', None))
        recipe = attrs.get('recipe', getattr(self.instance, 'recipe', None))
        if bool(product) == bool(recipe):
            raise serializers.ValidationError('Выберите либо product, либо recipe.')
        if attrs.get('grams', getattr(self.instance, 'grams', 0)) < 0:
            raise serializers.ValidationError({'grams': 'Вес не может быть отрицательным.'})
        if attrs.get('servings', getattr(self.instance, 'servings', 0)) < 0:
            raise serializers.ValidationError({'servings': 'Количество порций не может быть отрицательным.'})
        return attrs
