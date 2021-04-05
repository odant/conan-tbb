/*
    Copyright (c) 2005-2021 Intel Corporation

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

#ifndef __TBB_test_common_iterator_H
#define __TBB_test_common_iterator_H

#include <iterator>
#include <memory>
#include <atomic>
#include "utils_assert.h"

namespace utils {

template <typename T>
class InputIterator {
public:
    typedef std::input_iterator_tag iterator_category;
    typedef T value_type;
    typedef typename std::allocator<T>::difference_type difference_type;
    typedef typename std::allocator_traits<std::allocator<T>>::pointer pointer;
    typedef typename std::allocator<T>::value_type& reference;

    explicit InputIterator ( T * ptr ) : my_ptr(ptr), my_shared_epoch(new Epoch), my_current_epoch(0) {}

    InputIterator( const InputIterator& it ) {
        REQUIRE_MESSAGE(it.my_current_epoch == it.my_shared_epoch->epoch, "Copying an invalidated iterator");
        my_ptr = it.my_ptr;
        my_shared_epoch = it.my_shared_epoch;
        my_current_epoch = it.my_current_epoch;
        ++my_shared_epoch->refcounter;
    }

    InputIterator& operator= ( const InputIterator& it ) {
        REQUIRE_MESSAGE(it.my_current_epoch == it.my_shared_epoch->epoch, "Assigning an invalidated iterator");
        my_ptr = it.my_ptr;
        my_current_epoch = it.my_current_epoch;
        if(my_shared_epoch == it.my_shared_epoch)
            return *this;
        destroy();
        my_shared_epoch = it.my_shared_epoch;
        ++my_shared_epoch->refcounter;
        return *this;
    }

    T& operator* () const {
        REQUIRE_MESSAGE(my_shared_epoch->epoch == my_current_epoch, "Dereferencing an invalidated input iterator");
        return *my_ptr;
    }

    InputIterator& operator++ () {
        REQUIRE_MESSAGE(my_shared_epoch->epoch == my_current_epoch, "Incrementing an invalidated input iterator");
        ++my_ptr;
        ++my_current_epoch;
        ++my_shared_epoch->epoch;
        return *this;
    }

    bool operator== ( const InputIterator& it ) const {
        REQUIRE_MESSAGE(my_shared_epoch->epoch == my_current_epoch, "Comparing an invalidated input iterator");
        REQUIRE_MESSAGE(it.my_shared_epoch->epoch == it.my_current_epoch, "Comparing with an invalidated input iterator");
        return my_ptr == it.my_ptr;
    }

    ~InputIterator() {
        destroy();
    }
private:
    void destroy() {
        if(0 == --my_shared_epoch->refcounter) {
            delete my_shared_epoch;
        }
    }
    struct Epoch {
        typedef std::atomic<size_t> Counter;
        Epoch() { epoch = 0; refcounter = 1; }
        Counter epoch;
        Counter refcounter;
    };

    T * my_ptr;
    Epoch *my_shared_epoch;
    size_t my_current_epoch;
};

template <typename T>
class ForwardIterator {
    T * my_ptr;
public:
    typedef std::forward_iterator_tag iterator_category;
    typedef T value_type;
    typedef typename std::allocator<T>::difference_type difference_type;
    typedef typename std::allocator_traits<std::allocator<T>>::pointer pointer;
    typedef typename std::allocator<T>::value_type& reference;

    explicit ForwardIterator ( T * ptr ) : my_ptr(ptr){}

    ForwardIterator ( const ForwardIterator& r ) : my_ptr(r.my_ptr){}
    T& operator* () const { return *my_ptr; }
    ForwardIterator& operator++ () { ++my_ptr; return *this; }
    bool operator== ( const ForwardIterator& r ) const { return my_ptr == r.my_ptr; }
};

template <typename T>
class RandomIterator {
    T * my_ptr;
public:
    typedef std::random_access_iterator_tag iterator_category;
    typedef T value_type;
    typedef typename std::allocator_traits<std::allocator<T>>::pointer pointer;
    typedef typename std::allocator<T>::value_type& reference;
    typedef typename std::allocator<T>::difference_type difference_type;

    explicit RandomIterator ( T * ptr ) : my_ptr(ptr){}
    RandomIterator ( const RandomIterator& r ) : my_ptr(r.my_ptr){}
    T& operator* () const { return *my_ptr; }
    RandomIterator& operator++ () { ++my_ptr; return *this; }
    bool operator== ( const RandomIterator& r ) const { return my_ptr == r.my_ptr; }
    bool operator!= ( const RandomIterator& r ) const { return my_ptr != r.my_ptr; }
    difference_type operator- (const RandomIterator &r) const {return my_ptr - r.my_ptr;}
    RandomIterator operator+ (difference_type n) const {return RandomIterator(my_ptr + n);}
    bool operator< (const RandomIterator &r) const {return my_ptr < r.my_ptr;}
};

template <typename T>
class ConstRandomIterator {
    const T * my_ptr;
public:
    typedef std::random_access_iterator_tag iterator_category;
    typedef const T value_type;
    typedef typename std::allocator_traits<std::allocator<T>>::const_pointer pointer;
    typedef const typename std::allocator<T>::value_type& reference;
    typedef typename std::allocator<T>::difference_type difference_type;

    explicit ConstRandomIterator ( const T * ptr ) : my_ptr(ptr){}
    ConstRandomIterator ( const ConstRandomIterator& r ) : my_ptr(r.my_ptr){}
    const T& operator* () const { return *my_ptr; }
    ConstRandomIterator& operator++ () { ++my_ptr; return *this; }
    bool operator== ( const ConstRandomIterator& r ) const { return my_ptr == r.my_ptr; }
    bool operator!= ( const ConstRandomIterator& r ) const { return my_ptr != r.my_ptr; }
    difference_type operator- (const ConstRandomIterator &r) const {return my_ptr - r.my_ptr;}
    ConstRandomIterator operator+ (difference_type n) const {return ConstRandomIterator(my_ptr + n);}
    bool operator< (const ConstRandomIterator &r) const {return my_ptr < r.my_ptr;}
};

} // namespace utils

#endif // __TBB_test_common_iterator_H
