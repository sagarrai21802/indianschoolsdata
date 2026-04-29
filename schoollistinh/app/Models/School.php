<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Support\Collection;

class School extends Model
{
    use HasFactory;

    protected $fillable = [
        'city_id',
        'locality_id',
        'name',
        'slug',
        'address',
        'locality_name',
        'board',
        'medium',
        'school_type',
        'established',
        'grades',
        'fees_min',
        'fees_max',
        'fees_currency',
        'fees_text',
        'phone',
        'email',
        'website',
        'rating',
        'reviews_count',
        'json_data',
        'images',
        'admission_status',
        'is_active',
        'is_featured',
        'is_verified',
    ];

    protected $casts = [
        'fees_min' => 'integer',
        'fees_max' => 'integer',
        'rating' => 'decimal:1',
        'reviews_count' => 'integer',
        'json_data' => 'array',
        'images' => 'array',
        'is_active' => 'boolean',
        'is_featured' => 'boolean',
        'is_verified' => 'boolean',
    ];

    public function city(): BelongsTo
    {
        return $this->belongsTo(City::class);
    }

    public function locality(): BelongsTo
    {
        return $this->belongsTo(Locality::class);
    }

    public function facilities(): BelongsToMany
    {
        return $this->belongsToMany(Facility::class);
    }

    public function scopeActive($query)
    {
        return $query->where('is_active', true);
    }

    public function scopeFeatured($query)
    {
        return $query->where('is_featured', true);
    }

    public function scopeByBoard($query, string $board)
    {
        return $query->where('board', $board);
    }

    public function scopeByType($query, string $type)
    {
        return $query->where('school_type', $type);
    }

    public function scopeByLocality($query, string $localitySlug)
    {
        return $query->whereHas('locality', function ($q) use ($localitySlug) {
            $q->where('slug', $localitySlug);
        });
    }

    public function scopeMinRating($query, float $rating)
    {
        return $query->where('rating', '>=', $rating);
    }

    public function scopeFeeRange($query, ?int $min = null, ?int $max = null)
    {
        if ($min !== null) {
            $query->where(function ($q) use ($min) {
                $q->where('fees_min', '>=', $min)
                  ->orWhere('fees_max', '>=', $min);
            });
        }
        
        if ($max !== null) {
            $query->where(function ($q) use ($max) {
                $q->where('fees_min', '<=', $max)
                  ->orWhere('fees_max', '<=', $max)
                  ->orWhereNull('fees_min');
            });
        }
        
        return $query;
    }

    public function getDisplayFeesAttribute(): string
    {
        if ($this->fees_min && $this->fees_max) {
            return '₹' . number_format($this->fees_min) . ' - ₹' . number_format($this->fees_max);
        } elseif ($this->fees_min) {
            return '₹' . number_format($this->fees_min) . '+';
        } elseif ($this->fees_max) {
            return 'Up to ₹' . number_format($this->fees_max);
        }
        return 'Contact for fees';
    }

    public function getPrimaryImageAttribute(): ?string
    {
        if (!empty($this->images) && is_array($this->images)) {
            return $this->images[0] ?? null;
        }
        return null;
    }

    public function getRouteKeyName(): string
    {
        return 'slug';
    }

    public function getUrlAttribute(): string
    {
        return route('school.show', [
            'city' => $this->city->slug,
            'school' => $this->slug,
        ]);
    }

    public function toSearchableArray(): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'address' => $this->address,
            'board' => $this->board,
            'school_type' => $this->school_type,
            'locality' => $this->locality_name,
            'city' => $this->city?->name,
        ];
    }
}
