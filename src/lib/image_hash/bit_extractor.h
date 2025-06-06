/* This code is subject to the terms of the Mozilla Public License, v.2.0. http://mozilla.org/MPL/2.0/. */
#pragma once

#include <iostream>
#include <tuple>

// 2(?) <= READLEN <= 8
template<typename C, size_t N, size_t READLEN>
class bit_extractor
{
protected:
	static constexpr uint64_t BITMASK = (1 << READLEN) - 1; // e.g. 0xFF, 0x1F, 0xF

public:
	template <size_t iterations=READLEN>
	static constexpr auto get_offsets(unsigned offset)
	{
		if constexpr (iterations == 1)
			return std::make_tuple(offset);
		else
			return std::tuple_cat(std::make_tuple(offset), get_offsets<iterations-1>(offset+READLEN+2));
	}

	static constexpr auto pattern(unsigned id)
	{
		// convert our numbering scheme in extract_fast() into the bitpositions
		// that we'll use to extract our (e.g.) 64 bits (8x8) from the 100 bits (10x10) we have.
		return get_offsets(id%3 + (id/3)*(READLEN+2));
	}

public:
	bit_extractor(const C& bits)
		: _bits(bits)
	{}

	template<typename... T>
	uint64_t extract()
	{
		return 0;
	}

	template<typename... T>
	uint64_t extract(unsigned bit_offset, const T&... t)
	{
		constexpr auto byte_offset = sizeof...(T);
		
		// 确保位操作的安全性和一致性
		constexpr size_t shift_amount = N - READLEN;
		if (bit_offset > shift_amount) {
			return extract(t...);
		}
		
		// 分步进行位操作以避免编译器差异
		C shifted = _bits >> (shift_amount - bit_offset);
		C masked = shifted & static_cast<C>(BITMASK);
		uint64_t bits_value = static_cast<uint64_t>(masked);
		
		uint64_t total = bits_value << (byte_offset * READLEN);
		return total | extract(t...);
	}

	template <typename Tuple, size_t... I>
	constexpr uint64_t extract_tuple(Tuple const& tuple, std::index_sequence<I...>) {
		return extract(std::get<I>(tuple)...);
	}

	template <typename Tuple>
	constexpr uint64_t extract_tuple(Tuple const& tuple) {
		return extract_tuple(tuple, std::make_index_sequence<std::tuple_size<Tuple>::value>());
	}


protected:
	C _bits;
};
