from rest_framework import serializers
from django.contrib.auth.models import User
from api.models import UserProfile, Ward, WardPrediction


class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = ['id', 'ward_no', 'ward_name']


class UserProfileSerializer(serializers.ModelSerializer):
    ward_details = WardSerializer(source='ward', read_only=True)

    class Meta:
        model = UserProfile
        fields = ['role', 'ward', 'ward_details', 'phone', 'created_at']


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']


MUMBAI_WARDS = [
    'A', 'B', 'C', 'D', 'E', 'F/N', 'F/S', 'G/N', 'G/S',
    'H/E', 'H/W', 'K/E', 'K/W', 'L', 'M/E', 'M/W', 'N',
    'P/N', 'P/S', 'R/C', 'R/N', 'R/S', 'S', 'T',
]

class RegisterSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, default='citizen')
    ward_name = serializers.ChoiceField(choices=MUMBAI_WARDS, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=15, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'role', 'ward_name', 'phone']

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already taken.')
        return value

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already registered.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password2'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop('role', 'citizen')
        ward_name = validated_data.pop('ward_name', '')
        phone = validated_data.pop('phone', '')
        password = validated_data.pop('password')

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        profile = user.profile
        profile.role = role
        profile.phone = phone
        if ward_name:
            ward = Ward.objects.filter(ward_name=ward_name).first()
            if ward:
                profile.ward = ward
        profile.save()

        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)


class WardPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WardPrediction
        fields = '__all__'
