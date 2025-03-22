import React, { useState } from 'react';
import { ChakraProvider, VStack, Container, Heading, useToast } from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { QueryForm } from './components/QueryForm';
import { ResultDisplay } from './components/ResultDisplay';
import { QueryResponse } from './types';


const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const toast = useToast();

  const handleQuerySubmit = (result: QueryResponse) => {
    setQueryResult(result);
  };

  const handleError = (error: Error) => {
    toast({
      title: 'Error',
      description: error.message,
      status: 'error',
      duration: 5000,
      isClosable: true,
    });
  };

  return (
    <QueryClientProvider client={queryClient}>
      <ChakraProvider>
        <Container maxW="container.xl" py={8}>
          <VStack spacing={8} align="stretch">
            <Heading as="h1" size="xl" textAlign="center">
              RAG Research Paper Assistant
            </Heading>
            <QueryForm 
              onSubmit={handleQuerySubmit}
              onError={handleError}
            />
            {queryResult && <ResultDisplay result={queryResult} />}
          </VStack>
        </Container>
      </ChakraProvider>
    </QueryClientProvider>
  );
}

export default App;
