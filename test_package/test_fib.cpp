#include <tbb/task_group.h>
#include <iostream>
#include <cstdlib>


int Fib(int n) {

    if(n < 2) {
        return n;
    } else {
        int x, y;
        tbb::task_group g;
        g.run([&]{ x=Fib(n-1); });  // spawn a task
        g.run([&]{ y=Fib(n-2); });  // spawn another task
        g.wait();                   // wait for both tasks to complete
        return x+y;
    }
}

int main(int, char**) {

    std::cout << "Fib 6=" << Fib(6) << std::endl;
    
    return EXIT_SUCCESS;
}