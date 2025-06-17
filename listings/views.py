
"""
API Views for the listings app.
This file contains Viewswts that provide RESTful API endpoints for:
- LISTING (property management)
- BOOKING (reserversation system)
- REVIEWS (user feedback)
- USERPROFILE  (user management)
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q, Avg
from datetime import date, datetime, timedelta



from .models import UserProfile, Listing, Booking, Review
from .serializers import (
    UserProfileSerializer,
    ListingSerializer,
    BookingSerializer,
    ReviewSerializer
)

from .filters import ListingFilter, BookingFilter

class UserProfileVViews(viewsets.ModelViewSet):
    """
    Viewsets for managing user profiles

    It provides various endpoints for CRUD operations
    -GET /api/v1/users - List all user profiles
    -GET /api/v1/users/{id} - Get specific user profle
    -POST /api/v1/users - Create a new user
    -PUT /api/v1/users/{id} - Update the user profile
    -DELETE /api/v1/users{id} - Delet the user profile
    
    """
    querysey = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'user_id'

    # Filtering and searching
    filter_backend = [DjangoFilterBackend. filters.SearchFilter]
    filterset_fields = ['role', 'email_verifief']
    search_fields = ['user__username', 'user__email', 'user__firstname', 'user__last_name']

    def get_permissions(self):
        """
        Instantiate and return the list of permissions that are required for this views
        """
        if self.action == 'list':
            # Anyone can view the list (for hosts, etc)
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        elif self.action == 'create':
            # ANyone can create the account
            permission_classes = [permissions.AllowAny]
        else:
            # Only authenticated users can view or update their profiles
            permission_clasess = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods = ['get'], permission_classes =[permissions.IsAuthenticated])
    def me(self, request):
        """
        Get the current user's profile
        GET /api/v1/users/me
        """
        try:
            profile = UserProfile.objects.get(user = request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except UserProfile.DoesNotExist:
            return Response({
                'error': 'Profile not found'
            }, status= status.HTTP_404_NOT_FOUND)
        
    @action(detail=False, methods =['get'])
    def listings(self, request, user_id=None):
        """
        
        Get all listings for a specific user (host)
        Get /api/v1/{id}/listings """

        user_profile = self.get_object()
        listings = Listing.objects.filter(host = user_profile)

        # APply pagination if needed
        page = self.paginate_queryset(listings)
        if page is not None:
            serializer = ListingSerializer(page, many =True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ListingSerializer(listings, many =True)
        return Response(serializer.data)
    
    @action (detail = False, methods =['get'])
    def bookings(self, request, user_id = None):
        """
        Get all bookings for a specific user
        Get api/v1/users/{id}/bookings"""

        user_profile = self.get_object()
        bookings = Booking.objects.filter(user=user_profile)

        # Add pagination if needed 
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = BookingSerializer(page, many = True)
            return self.get_paginated_response(serializer.data)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)
    
class ListingViews(viewsets.ModelViewSet): # This line tells DRF to generate CRUD API endpoints using the listing model
    """
    Viesets for managing property listings
    This provides endpoints for: 
    -GET /api/v1/listings = List all property listings
    -GET /api/v1/listing/{id}/ = Get specific listings 
    -POST /api/v1/listings/ = create a new property listing
    -PUT /api/v1/listings/{id} = update listing
    - DELETE /api/v1/listings/{id} = delet listing

    # Additional endpoints
     - GET /api/v1/listings/{id}/reviews = Get reviews for all listing
     - GET /api/v1/listings/{id}/bookings = Advances search

    """

    serializer_class = ListingSerializer  # Ths lie tells django to use the listing serializer for serializing and deserializing data to and from JSON
    lookup_field = 'property_id'  # Customizes the field used in URLS lookup 

    # Filtering, searching and ordering
    filter_backends = [DjangoFilterBackend, filter.SearchFilter, filter.OrderingFilter]
    filterset_class = ListingFilter # Custom filter class (we'll recreate this)
    search_fields = ['name', 'description', 'city', 'county']
    ordering_fields = ['price_per_night', 'created_at', 'name']
    ordering = ['-created_at'] # Default ordering (newest first)

    def get_queryset(self):   # only return approved listings only
        """
        Customize queryset based on user permissions and filters"""

        if self.action =='list':
            # Base queryset only approved listings for general users
            # For list view, only show approved listings
            return Listing.objects.filter(status = 'approved').select_related('host__user')  #It optimizes the DB queries by joining foreign keys
        else:
            # For detail/create/update/delete, show all listings
            return Listing.objects.all().select_related('host__user')
        

    def get_permissions(self):
        """Set permissions based on actions"""

        if self.action in ['list', 'retrieve']:
            # Anyone can view listings
            permission_classes = [permissions.AllowAny]
        elif self.action =='create':
            # Only authentcated users can create listings
            permission_classes = [permissions.IsAuthenticated]
        else:
            # only listing owners can update or delete
            permission_classess = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):   # This function is called when someone creats a new listing, it ensures that the user has a profile and if not has to create one and it also ensures that they are marked as a host
        """
        Set the host to the current user when creating a listing"""
        # Get or create user profile for the current user
        user_profile, created = UserProfile.objects.get_or_create(
            user = self.request.user,
            defaults = {'role': 'host'}
        )

        # If the user is not a host, update their role
        if user_profile.role != 'host':
            user_profile.role = 'host'
            user_profile.save()

        serializer.save(host = user_profile)
    @action(detail = True, methods=['get'])   # @action decorator is used in viewsets to create custom endpoints that do not follow the standard REST patterns like (list, retrieve, CRUD operations), detail = True means that the route operates on a single object that is listings/{id}/ reviews  and get method means that it will only respond to GET requests only. 
    def reviews(self, request, property_id = None): # Custom endpoint for the listing 
        """
        Get all reviews for a specific listing
        GET /api/v1/listings/{id}/reviews"""

        listing = self.get_object()
        reviews = Review.objects.filter(property=listing).select_related('user__user')

        # Apply pagination if needed
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many = True)
            return self.get_paginated_response(serializer.data)
        serializer = ReviewSerializer(reviews, manay =True)
        return Response(serializer.data)
    
    @action (detail = True, methods=['get'])  # Without the action decorator we would have to create a separate API view or function view
    def availability(self, request, property_id= None):
        """
        Cehck for availabikty for a listing on specific dataes.
        GET /api/v1/listings/{id}/availability? start_date=2024-01-01&end_date=2024
        """
        listing = self.get_object()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required.'},
                                status=status.HTTP_400_BAD_REQUEST             
            )
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status = status.HTTP_400_BAD_REQUEST
            )
            

        #Check for conflicting bookings
        conflicting_bookings = Booking.objects.filter(
            property = listing,
            status__in = ['pending', 'confirmed'],
            start_date__lt = end_date,
            end_date__gt = start_date
        )

        is_available = not conflicting_bookings.exists()

        return Response({
            'available': is_available,
            'start_date': start_date,\
            'end_date' : end_date,
            'conflicting_bookings': conflicting_bookings.count()
        })
    @action(detail = False, methods =['get'])
    def search(self, request):
        """ Advanced search for listings
        GET /api/v1/listing/search/?city=NeW yORK& min_price = 100& max_price =300"""

        queryset = self.get_queryset()

        # Location search
        city = request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)

        #  Price range seafch
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')

        if min_price:
            queryset = queryset.filter(price_per_night__gte = min_price)
        if max_price:
            queryset = queryset. filter(price_per_night__lte = max_price)

        # Property specifications
        bedrooms = request.query_params.get('bedrooms')
        if bedrooms:
            queryset = queryset.filter(bedrooms__gte=bedrooms)
        
        guests = request.query_params.get('guests')
        if guests:
            queryset = queryset.filter(max_guests__gte= guests)

        # Apply pagination if needed
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many =True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_srializer(queryset, many =True)
        return Response(serializer.data)
    

class BookingViews(viewsets.ModelViewSet):
    """
    Viewsets for managing bookings
    Its provides the endpoints for:
     -GET /api/v1/bookings/ -Lists the user's bookings
     -GET /api/v1/bookings/{id}/n - Gets the specific booking
     -POST /api/v1/bookings - creates  a new booking
     -PUT /api/v1/bookings/{id}/ - updates the booking
     -DELETE /api/v1/bookings/{id}/ - Cancels the booking"""
    
    serializer_class = BookingSerializer # Tells the viewset to use the Booking serializer for serialzing and deserializing

    lookup_field = 'booking_id'
    permission_classes = [permissions.IsAuthenticated]

    #  Filtering, searching and ordering
    filter_backends = [DjangoFilterBackend, filter.OrderingFilter]
    filterset_class = ListingFilter # custom filyer class (to be created)
    search_fields = ['name', 'description', 'city', 'county']
    ordering_fields = ['price_per_night', 'created_at','name']
    ordering = ['-created_at'] # Default ordering (newest first)

    def get_queryset(self):
        """
        Return the bookings based on the user role
        -guests see their own bookings
        - Hosts see bookings for their properties
        -AAdmins see all the bookings
        """

        user = self.request.user 

        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Booking.objects.none()
        
        if user_profile.role == 'admin':
            # Admins can see all the bookings
            return Booking.objects.all().select_related('property', 'user__user')
        elif user_profile.role =='host':
            # Hosts see their own bookings
            return Booking.objects.filter(
                user = user_profile,
            ).select_related('property', 'user__user')
        else:
            # Guests see their own bookings
            return Booking.objects.filter(user= user_profile).select_related('property', 'user__user')
        
    def perform_create(self, serializer):
        """ Set the user to the current user when creating a booking"""
        user_profile, created = UserProfile.objects.get_or_create(
            user = self.request.user,
            defaults = {'role': 'guest'}
        )

        # Get the object losting
        property_id = serializer.validated_data.get('property_id')
        listing = get_object_or_404(Listing, property_id = property_id)
        # calculate the total price
        start_date  = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        nights = (end_date - start_date).days
        total_price = nights * listing.price_per_night

        serializer.save(
            user = user_profile,
            property = listing,
            total_price = total_price
        )

    @action(detail =True, methods =['post'])
    def confirm(self, request, booking_id =None):
        """
        Confirm a pending booking(host only)
        POST /api/v1/booking/{id}/confirm
        """
        booking = self.get_object()
        user_profile = UserProfile.object.get(user = request.user)
        if booking.property.host != user_profile:
            return Response(
                {'error': 'Only the property host can confirm bookings'}, status =status.HTTP_400_BAD_REQUEST                    
            )
        booking.status =  'confirmed'
        booking.save()

        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    
    @action(detail =True, methods = ['post'])
    def cancel(self,reuqest, booking_id = None):
        """
        Cancel the booking
        POST /api/v1/bookings/{id}/cancel
        """

        booking = self.get_object()
        # Check permissions(guests and host can cancel)
        user_profile = UserProfile.objects.get(user = request.user)
        if booking.user != user_profile and booking.property.host != user_profile:
            return Response(
                {'error': 'You can only cancel your own bookings or those of your properties'},
                status=status.HTTP_403_FORBIDDEN
            )
        booking.status = 'cancelled'
        booking.save()

        serializer = self.get_serializer(booking)
        return Response(serializer.data)
    

class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing reviews.
    
    Provides endpoints for:
    - GET /api/v1/reviews/ - List reviews
    - GET /api/v1/reviews/{id}/ - Get specific review
    - POST /api/v1/reviews/ - Create new review
    - PUT /api/v1/reviews/{id}/ - Update review
    - DELETE /api/v1/reviews/{id}/ - Delete review
    """
    
    serializer_class = ReviewSerializer
    lookup_field = 'review_id'
    permission_classes = [permissions.IsAuthenticated]
    
    # Filtering and ordering
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['rating', 'property']
    ordering_fields = ['rating', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return reviews based on user role.
        """
        user = self.request.user
        
        try:
            user_profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return Review.objects.none()
        
        if user_profile.role == 'admin':
            # Admins can see all reviews
            return Review.objects.all().select_related('user__user', 'property')
        elif user_profile.role == 'host':
            # Hosts see reviews for their properties
            return Review.objects.filter(
                property__host=user_profile
            ).select_related('user__user', 'property')
        else:
            # Guests see reviews they've written
            return Review.objects.filter(
                user=user_profile
            ).select_related('user__user', 'property')
    
    def perform_create(self, serializer):
        """
        Set the user to the current user when creating a review.
        """
        user_profile = UserProfile.objects.get(user=self.request.user)
        
        # Get booking and property
        booking_id = serializer.validated_data.get('booking_id')
        property_id = serializer.validated_data.get('property_id')
        
        booking = get_object_or_404(Booking, booking_id=booking_id)
        listing = get_object_or_404(Listing, property_id=property_id)
        
        serializer.save(
            user=user_profile,
            booking=booking,
            property=listing
        )
    
    @action(detail=True, methods=['post'])
    def respond(self, request, review_id=None):
        """
        Add host response to a review (host only).
        POST /api/v1/reviews/{id}/respond/
        """
        review = self.get_object()
        
        # Check if user is the host of the property
        user_profile = UserProfile.objects.get(user=request.user)
        if review.property.host != user_profile:
            return Response(
                {'error': 'Only the property host can respond to reviews'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        host_response = request.data.get('host_response')
        if not host_response:
            return Response(
                {'error': 'host_response is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.utils import timezone
        review.host_response = host_response
        review.host_response_date = timezone.now()
        review.save()
        
        serializer = self.get_serializer(review)
        return Response(serializer.data)
    